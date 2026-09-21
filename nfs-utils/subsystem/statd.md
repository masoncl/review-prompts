# NSM: rpc.statd and sm-notify

Applies to `utils/statd/` and `support/nsm/`.

`rpc.statd` implements the Network Status Monitor protocol so NLM (file
locking) can detect peer reboots. It is a **root-started, network-facing
daemon that drops privileges and writes files whose names derive from
wire-supplied strings**. That combination is why statd has a long CVE history,
and why this file is mostly about two things: name sanitisation and privilege
ordering.

`sm-notify` is the one-shot boot-time counterpart that blasts SM_NOTIFY to
every peer recorded in `/var/lib/nfs/sm`.

## Hostname → pathname sanitisation

`nsm_make_record_pathname()` (`support/nsm/file.c`) is the load-bearing
control. Everything under `/var/lib/nfs/sm/`, `sm.bak/` and the monitor
records is named after a peer-supplied `mon_name`:

```c
/*
 * Block hostnames that contain characters that have
 * meaning to the file system (like '/'), or that can
 * be confusing on visual inspection (like ' ').
 */
for (c = hostname; *c != '\0'; c++)
	if (*c == '/' || isspace((int)*c) != 0) {
		xlog(D_GENERAL, "Hostname contains invalid characters");
		return NULL;
	}
```

followed by a `PATH_MAX` bound and a checked `snprintf()`.

**Review rule.** Any new code that builds a filesystem path from `mon_name`,
`my_name`, or any other string arriving over SM_MON / SM_UNMON / SM_NOTIFY
must go through this function (or `nsm_make_pathname()`). Constructing the
path ad hoc — even "just for a temp file", even with a `snprintf()` bound — is
a path-traversal finding at CRITICAL severity. A bound on length is not a
substitute for rejecting `/`.

Related: the caller must free the returned buffer, and must handle `NULL`
(rejection) distinctly from an I/O error.

## Atomic on-disk updates

`nsm_atomic_write()` (`support/nsm/file.c`) writes to a temporary file with
`O_SYNC` and then `rename()`s it into place. Reuse it for any new persistent
NSM state rather than writing in place — statd can be killed at any moment,
and a half-written monitor record silently loses a peer, which means a missed
reboot notification and stale locks.

`nsm_get_state()` / the state-number file read and write a raw `int` with
`read(2)`/`write(2)`. That is fixed-width and host-endian. It is fine today
because the file is local, but a patch that widens the type, changes the
format, or contemplates a shared state directory needs to address
compatibility explicitly.

## Startup ordering

`utils/statd/statd.c` carries explicit `/* ORDER */` comments. The sequence is
a security and correctness contract:

1. **Unregister old listeners while still root.** `statd_unregister()` runs
   first, because rpcbind permission-checks unregistration by the requesting
   identity.
2. **Drop privileges.** `nsm_drop_privileges(pidfd)`.
3. **Create the RPC listeners after the drop**, so statd owns them as the
   unprivileged user and can therefore unregister them again at exit
   (`atexit(statd_unregister)`).
4. `daemon_ready()`.

Reordering any of these breaks something concrete: registering before the drop
leaves entries statd cannot clean up; unregistering after the drop fails
against rpcbind. **Treat a reordering patch here as needing an explicit
justification in the commit message.**

## The privilege drop itself

`nsm_drop_privileges()` (`support/nsm/file.c`) is the reference sequence for
the whole tree:

- `umask()`, `chdir()` into the state directory.
- `lstat()` the monitor directory to discover the target uid/gid — the owner
  of `/var/lib/nfs/sm` decides who statd becomes. A patch that hardcodes a uid
  changes deployment behaviour.
- Return early if already running unprivileged as that owner.
- `prune_bounding_set()`, keeping only `CAP_NET_BIND_SERVICE`.
- `fchown()` the **already-open pidfile fd**, so the pidfile stays writable
  after the drop (and so a state directory on NFS does not leave a stale fd).
- `prctl(PR_SET_KEEPCAPS, 1, ...)`.
- `setgroups(0, NULL)`.
- ```c
  /*
   * ORDER
   *
   * setgid(2) first, as setuid(2) may remove privileges needed
   * to set the group id.
   */
  if (setgid(st.st_gid) == -1 || setuid(st.st_uid) == -1)
  ```
- `nsm_clear_capabilities()`.

**Review rules:** `setgid()` before `setuid()`, always. Every step's return
value checked — an unchecked `setuid()` that fails leaves a root daemon
believing it dropped. `setgroups(0, NULL)` not omitted. No new operation
inserted between `PR_SET_KEEPCAPS` and the capability clear that could be
exploited with the retained capabilities.

## Pidfile handling

`create_pidfile()` / `truncate_pidfile()` (`utils/statd/statd.c`): unlink then
create, `dup()` the fd before `fclose()` so the daemon keeps an open handle
across the privilege drop, and truncate via `atexit()` rather than unlinking.

Note that `create_pidfile()` calls `xlog_err()` on `fopen()` failure and then
uses `fp` unconditionally. **That is correct** — `xlog_err()` does not return.
See the false-positive guide; do not report it.

## Signals

`statd.c` installs `SIGHUP`/`SIGINT`/`SIGTERM` → `killer()` (unregister, then
`exit(0)`), `SIGUSR1` → `sigusr()` (re-run notification), and ignores
`SIGCHLD` and `SIGPIPE`.

`SIGUSR1` collides with the xlog debug-level toggle installed by
`xlog_open()`. statd wins because it installs later. That is intentional here;
be aware of it when adding signal handling to any other daemon.

## sm-notify

- Runs once at boot, forks into the background, and retries peers with
  backoff. A change to the retry or timeout logic affects how long stale locks
  persist after a server reboot.
- Uses a reserved source port by default (`-p`), because some servers require
  it. Dropping that is an interoperability regression.
- Heavy `getaddrinfo()` use — all releases must be `nfs_freeaddrinfo()`.
- Reads and rewrites `/var/lib/nfs/sm` → `sm.bak`. Losing an entry here means
  a peer never learns about the reboot.

## Review Checklist

- [ ] Every path built from a wire-supplied name goes through
      `nsm_make_record_pathname()`.
- [ ] New persistent state uses `nsm_atomic_write()`.
- [ ] The `/* ORDER */` sequence in `statd.c` is intact.
- [ ] `setgid()` before `setuid()`; every drop step's return checked.
- [ ] XDR-decoded SM_MON/SM_NOTIFY arguments length-checked before use
      (see `sunrpc.md`).
- [ ] No new `xlog_err()` reachable from a request handler — statd would exit
      on remote input.
- [ ] `notlist` entries and `struct mon` allocations freed on the re-monitor
      and error paths (a real historical leak: an existing host re-monitoring
      in `sm_mon_1_svc()`).
- [ ] `daemon_ready()` still reached on every success path.
