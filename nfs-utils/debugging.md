# nfs-utils Debugging Protocol

Load `technical-patterns.md` first, then this file. Load subsystem guides from
`subsystem/subsystem.md` once you know which component is involved.

## STEP 1: Classify the failure

| Symptom | Likely component | Guide |
|---|---|---|
| `mount.nfs` fails, wrong error, hangs | `mount.nfs` | `subsystem/mount.md` |
| "access denied by server", export not visible | `exportfs`/`rpc.mountd` | `subsystem/export.md` |
| Locks not recovered after a reboot | `rpc.statd`/`sm-notify` | `subsystem/statd.md` |
| Everything maps to `nobody` | `rpc.idmapd` | `subsystem/upcalls.md` |
| Kerberos mount fails, context errors | `rpc.gssd`/`rpc.svcgssd` | `subsystem/upcalls.md` |
| Grace period wrong, clients not recovered | `nfsdcld`/`nfsdcltrack` | `subsystem/upcalls.md` |
| `rpc.nfsd`/`nfsdctl` errors, wrong thread or listener state | netlink | `subsystem/netlink.md` |
| A config option has no effect | `conffile.c` | `subsystem/config.md` |
| Works here, fails on another distribution | build configuration | `subsystem/build.md` |
| Daemon start hangs, systemd unit times out | `daemon_ready()` not reached | `technical-patterns.md` |

## STEP 2: Turn on the daemon's own logging

Every daemon uses xlog. Debug facilities are off by default and are the first
thing to enable — they are usually more informative than a strace.

- Most daemons take `-d`/`--debug` with a facility name (`general`, `call`,
  `auth`, `netlink`, `parse`, `all`). Check the man page for the exact
  spelling; `xlog_sconfig()` maps the names.
- `nfs.conf` has a `debug =` tag per daemon stanza.
- At runtime, `xlog_open()` installs `SIGUSR1`/`SIGUSR2` handlers that toggle
  the debug level, so `kill -USR1` can raise verbosity on a running daemon —
  **except** where the daemon installed its own `SIGUSR1` handler. `rpc.statd`
  does, and uses it to re-trigger notification instead.
- Output goes to syslog, and also to stderr while running in the foreground.
  Running the daemon in the foreground (`-F`) is usually the fastest route.

## STEP 3: Look at the state the daemon exposes

Read-only inspection, roughly in order of usefulness:

```
/proc/fs/nfsd/                 threads, versions, portlist, export_features
/proc/net/rpc/*/content        the kernel's export, expkey and auth caches
/proc/net/rpc/*/channel        the upcall channel (do not read it casually;
                               a read consumes a pending upcall)
/proc/self/mountstats          per-mount client counters
/sys/kernel/sunrpc/            RPC client and transport state
/var/lib/nfs/etab              expanded export table
/var/lib/nfs/rmtab             MOUNT client list
/var/lib/nfs/sm/, sm.bak/      NSM monitor records
```

Tools that render these:

| Tool | Shows |
|---|---|
| `exportfs -v` | the effective export table |
| `showmount -e <host>` | what a server advertises over MOUNT |
| `nfsdctl` (subcommands, or its REPL) | nfsd threads, versions, listeners |
| `rpcctl` | `/sys/kernel/sunrpc` — clients, transports, xprt switches |
| `nfsdclnts` | NFSv4 clients and their state on the server |
| `nfsstat` | RPC call counts, client and server |
| `mountstats`, `nfsiostat` | per-mount latency and operation breakdown |
| `nfsdclddb` | dump or repair the nfsdcld sqlite database |
| `rpcinfo -p`, `rpcinfo -s` | what is registered with rpcbind |
| `rpcdebug -m nfsd -s all` | kernel-side nfsd/sunrpc debug flags |
| `nfsconf --dump` | the merged `nfs.conf` as the parser sees it |

`nfsconf --dump` deserves special mention: config problems are frequently
"the value is in a file that loses the override", and the dump settles it
without reading `conffile.c`. See `subsystem/config.md` for the load order.

## STEP 4: Establish where the boundary is

nfs-utils sits between a remote peer, the kernel, and local configuration.
Decide which side the failure is on before reading code:

- **Wire.** `tcpdump -s0 -w /tmp/nfs.pcap port 2049 or port 111 or port 20048`,
  then read it in wireshark. This answers "did the server actually refuse, or
  did we never ask" faster than anything else.
- **Kernel/userspace boundary.** Watch the upcall. For the qword channels,
  a stuck mount with `rpc.mountd` idle usually means an upcall was consumed
  and never answered. For `rpc_pipefs` daemons, check that the pipe directory
  for the client actually exists and that the daemon has an inotify watch on
  it.
- **Config.** `nfsconf --dump`, and check what the systemd unit passes on the
  command line — a flag on the unit line overrides `nfs.conf`.
- **Build.** `<daemon> -v`, and check whether the feature was compiled in at
  all. A silently missing feature is usually a `--disable-` at package build
  time; see `subsystem/build.md`.

## STEP 5: Reproduce under a debugger or sanitiser

- Run the daemon in the foreground with `-F` and full debug.
- For crashes: `coredumpctl gdb <daemon>`, or run under gdb directly. Note
  that `daemon_init()` forks unless `-F` is given, so attach after the fork or
  use `-F`.
- For leaks in a daemon: `valgrind --leak-check=full --track-origins=yes` on
  the foreground process, then exercise the specific upcall or RPC. Most leaks
  in this tree are per-request and only show under repetition.
- For gssd, which is threaded: `valgrind --tool=helgrind`, or build with
  `-fsanitize=thread`. Refcount races on `struct clnt_info` are the recurring
  bug.
- `tests/test-lib.sh` gives you `start_statd`/`kill_statd` if you need a
  controlled statd; `tests/nsm_client` drives SM_MON/SM_UNMON directly.

## STEP 6: Read the code with the right expectations

Before concluding that code is wrong, check it against
`false-positive-guide.md`. In particular, when a daemon "exits for no reason",
look for an `xlog_err()` on the path — it calls `exit(1)`, and that is the
most common explanation for a daemon that vanishes without a crash.

Other high-yield checks when a daemon misbehaves rather than crashes:

- Did it reach `daemon_ready()`? If not, the parent never returns and systemd
  reports a timeout, not a failure.
- Did the privilege drop succeed? An unchecked `setuid()` leaves it root; a
  successful one may leave it unable to write a file it created earlier.
- Is the state directory owned by the user the daemon drops to?
  `nsm_drop_privileges()` derives the target uid from the directory owner.
- Is `rpc_createerr` being read after a second RPC call overwrote it? That
  produces confidently wrong error messages.

## Output

Produce `debug-report.txt`: the symptom, the evidence gathered at each step,
the specific code path implicated with file and function, and the proposed
fix or the next experiment. Distinguish clearly between what you observed and
what you inferred.
