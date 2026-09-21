# Netlink (nfsdctl, nfsd/lockd/sunrpc generic netlink)

Applies to `utils/nfsdctl/`, `support/nfs/nfsdnl.c`, `utils/nfsstat/`,
`utils/exportfs/`, `support/export/cache.c`, and the bundled uapi headers.

nfs-utils talks to the kernel's `nfsd`, `lockd` and `sunrpc` generic netlink
families using **libnl3** (`libnl-3.0` and `libnl-genl-3.0`, both required
unconditionally by `configure.ac`).

## Reachability: nfsdctl is not just an interactive tool

Do not rate an `nfsdctl` bug down on the assumption that it only affects
someone typing at a prompt. `systemd/nfs-server.service` starts and stops the
server through it:

```
ExecStart=/bin/sh -c '/usr/sbin/nfsdctl autostart || /usr/sbin/rpc.nfsd'
ExecStop=/bin/sh  -c '/usr/sbin/nfsdctl threads 0 || /usr/sbin/rpc.nfsd 0'
```

`autostart` runs `read_nfsd_conf()`, which walks the `nfs.conf` listener
settings through `add_listener()` into `update_listeners()`. So the listener
reconciliation path executes on **every normal server start**, with whatever
the administrator put in `nfs.conf`. A defect there misconfigures a
long-running daemon on boot — see the control-tool clause in the severity
rubric in `../review-core.md`.

Note also the `||` fallback: if `nfsdctl` exits non-zero the unit silently
falls back to `rpc.nfsd`. A bug that makes `nfsdctl` fail cleanly is therefore
masked at boot, while a bug that makes it *succeed wrongly* is not.

## Generated uapi headers — do not hand-edit

`support/include/nfsd_netlink.h`, `lockd_netlink.h`, `sunrpc_netlink.h` are
bundled copies of kernel uapi headers, carrying the banner:

```
/* Do not edit directly, auto-generated from: */
/*   Documentation/netlink/specs/nfsd.yaml */
/* YNL-GEN uapi header */
/* To regenerate run: tools/net/ynl/ynl-regen.sh */
```

**Reject any diff to these files that is not an exact regeneration.** A
hand-added enum value or attribute will diverge from the kernel and break as
soon as the real header lands.

The bundled copy is a fallback for build hosts with stale kernel headers.
`configure.ac` decides which to use by *compile-probing the system header for
a specific recent symbol*:

```m4
AC_COMPILE_IFELSE([AC_LANG_PROGRAM([[#include <linux/nfsd_netlink.h>]],
                                   [[int foo = NFSD_CMD_SERVER_STATS_GET;]])],
                  [AC_DEFINE([USE_SYSTEM_NFSD_NETLINK_H], 1, ...)])
```

Currently probed: `NFSD_CMD_SERVER_STATS_GET` (nfsd),
`LOCKD_CMD_SERVER_GET` (lockd), `SUNRPC_CMD_CACHE_NOTIFY` (sunrpc).

**Review rule:** a patch that syncs a header and then uses a *newer* symbol
than the probe tests is broken on hosts whose system header is older than the
new symbol but new enough to pass the probe — the build picks the system
header and the new symbol is missing. When new attributes or commands are
consumed, the probe symbol in `configure.ac` must be bumped to one of them.
Check this on every "sync `*_netlink.h` with the kernel" patch.

## Transaction skeleton

Every netlink call in `utils/nfsdctl/nfsdctl.c` follows the same shape. New
commands should match it rather than invent their own wiring:

```c
sock = netlink_sock_alloc();              /* nl_socket_alloc + genl_connect */
msg  = netlink_msg_alloc(sock, family);   /* nlmsg_alloc + genlmsg_put      */
ghdr = ...; ghdr->cmd = NFSD_CMD_...;
/* nla_put_* the attributes */
cb = nl_cb_alloc(NL_CB_CUSTOM);
nl_cb_err(cb, NL_CB_CUSTOM, error_handler, &ret);
nl_cb_set(cb, NL_CB_FINISH, NL_CB_CUSTOM, finish_handler, &ret);
nl_cb_set(cb, NL_CB_ACK,    NL_CB_CUSTOM, ack_handler,    &ret);
nl_cb_set(cb, NL_CB_VALID,  NL_CB_CUSTOM, recv_handler,   arg);
nl_send_auto(sock, msg);
while (ret > 0)
	nl_recvmsgs(sock, cb);
```

Check on every new transaction:

- All four callbacks installed. Omitting `NL_CB_ACK` or `NL_CB_FINISH` leaves
  the `nl_recvmsgs()` loop spinning or hanging.
- `ret` is the loop's sentinel and is written by the callbacks. A new path that
  does not clear it loops forever.
- `nlmsg_free(msg)`, `nl_cb_put(cb)`, `nl_socket_free(sock)` on **every** exit
  path, including the error branches added by the patch.
- The dump case (`NLM_F_DUMP`) delivers many `NL_CB_VALID` callbacks before
  `NL_CB_FINISH`; a handler that assumes one message is wrong.

## Runtime feature detection is mandatory

Userspace must keep working against older kernels. Do **not** gate on a
build-time `#ifdef` for a kernel feature; the kernel is not the build host.

The tree's mechanism is a `CTRL_CMD_GETPOLICY` query that records the highest
attribute index the running kernel's policy declares:

```c
int nfsd_threads_max_nlattr;
int nfsd_listener_max_nlattr;
/* filled in by query_nfsd_nl_policy() at startup */
```

then guards each newer attribute:

```c
if (nfsd_threads_max_nlattr < NFSD_A_SERVER_FH_KEY) { /* unsupported */ }
...
static bool userspace_rpcbind_supported(void)
{
	return nfsd_listener_max_nlattr >= NFSD_A_SERVER_SOCK_USERSPACE_RPCBIND;
}
```

**Review rule:** any use of an attribute or command newer than the oldest
supported kernel needs a matching max-attr check, and the failure path must
degrade gracefully — fall back to the old mechanism, or emit a clear
diagnostic. Silently sending an attribute the kernel does not know is rejected
by strict policy validation and surfaces as an opaque `EINVAL`.

## Kernel-supplied attributes are still untrusted

`nla_data()` payloads come from the kernel, but their *content* often
originates with a remote client (hostnames, addresses, paths relayed through
nfsd). Bound copies by the **actual attribute length**:

```c
/* insufficient on its own - caps by destination, not by source */
strncpy(sock->name, nla_data(a), MAX_CLASS_NAME_LEN);
sock->name[MAX_CLASS_NAME_LEN - 1] = '\0';
```

This is safe against overflow of `sock->name`, but it does not validate
`nla_len(a)`, so a shorter attribute is read past its end by `strncpy` up to
the first NUL. Prefer `nla_strlcpy()`/`nla_get_string()`, or check `nla_len()`
explicitly. Flag new attribute parsing that consults neither.

Also verify the parse policy: a `nla_parse()` with a policy array whose size
does not match the attribute enum will silently drop or misattribute values.

## Missing `break` in address-family switches

`-Wimplicit-fallthrough` is not enabled in this build (see
`../technical-patterns.md`), and address-family dispatch is common here.
Check every `switch (ss.ss_family)` / `switch (sa->sa_family)` for a `break`
on each case. A fallthrough from `AF_INET` into `AF_INET6` reinterprets a
`struct sockaddr_in` as a `struct sockaddr_in6` and compares fields past the
end of the smaller structure.

For contrast, `support/include/sockaddr.h` (`nfs_get_port()`,
`nfs_set_port()`) shows the correct form with explicit `break`s.

To judge how bad a given fallthrough is, you need the storage layout, so keep
these two facts to hand:

- `struct server_socket.ss` and anything else declared `struct
  sockaddr_storage` is large enough for either family. Reinterpreting it reads
  in-bounds, mostly-zero bytes — wrong answers, but not an over-read.
- `res->ai_addr` from `getaddrinfo()` is allocated only `res->ai_addrlen`
  bytes. For an `AF_INET` result that is `sizeof(struct sockaddr_in)`, so
  reading `sin6_addr` (16 bytes at offset 8) off it is a genuine heap
  over-read.

So the same missing `break` is "returns garbage" on one operand and
"reads out of bounds" on the other. Say which in the report.

## rpcbind registration from userspace

`utils/nfsdctl/rpcbind.c` and the `set_listeners()` path in `nfsdctl.c`
implement registration that the kernel used to do itself, enabled only when
`NFSD_A_SERVER_SOCK_USERSPACE_RPCBIND` is present. This runs as root and talks
to a local rpcbind. Points to check:

- Capability probe before use — `userspace_rpcbind_supported()`.
- The unregister sweep must precede registration; `rpcb_unset()` with no
  netconfig clears every netid at once and cannot selectively drop one of two
  TCP ports.
- Registration must not happen under a lock the kernel holds; the whole reason
  this moved to userspace is that synchronous rpcbind calls under
  `nfsd_mutex` tripped the hung-task watchdog.
- A failed rpcbind call warns and continues. NFSv4 does not need rpcbind, so
  aborting the whole operation is wrong.
- Teardown symmetry: entries registered when threads start must be cleared
  when the last thread stops, or they outlive the server and advertise a dead
  port.

## Cross-references

- `../../kernel/subsystem/nfsd.md`, "Netlink Interface" — the kernel side of
  these commands (when the kernel prompt set is installed).
- `config.md` — `nfs.conf` options that disable netlink and force the `/proc`
  fallback (`mountd`/`exportd` `no-netlink`).
- `build.md` — `--disable-nfsdctl` / `HAVE_NFSD_NETLINK` gating and the
  link-failure class it produces.
