# SunRPC / libtirpc

Applies to `support/nfs/{rpc_socket,getport,rpcmisc,rpcdispatch,svc_socket,
svc_create}.c`, `support/nsm/{rpc,sm_inter_*}.c`,
`support/export/mount_{clnt,xdr}.c`, `utils/showmount/`, and the RPC service
loops in `utils/statd/`, `utils/mountd/`, `utils/exportd/`.

## Dual TI-RPC / legacy-RPC paths

Almost everything touching `CLIENT *` or `svc_*` is bracketed by
`#ifdef HAVE_LIBTIRPC` / `#else`, driven by `AC_LIBTIRPC` in `configure.ac`
(`--enable-tirpc`, default yes). Examples: `support/nfs/rpc_socket.c`,
`support/nfs/getport.c`, `utils/mountd/svc_run.c`.

**Review rule:** new RPC client or server logic must supply *both* branches, or
explicitly justify why the feature is TI-RPC only (IPv6 and `AF_LOCAL`
transports genuinely are). A patch that only touches the `HAVE_LIBTIRPC` side
breaks the legacy build; a patch that only touches the `#else` side is dead
code on every modern distribution.

## Client creation

`nfs_get_rpcclient()` and `nfs_get_priv_rpcclient()` (`support/nfs/rpc_socket.c`)
are the sanctioned constructors. They dispatch on `sa_family`
(`AF_LOCAL`/`AF_INET`/`AF_INET6`) and protocol (`IPPROTO_TCP`/`IPPROTO_UDP`),
clear `rpc_createerr` up front via `nfs_clear_rpc_createerr()`, and set
`rpc_createerr.cf_stat` on every failure path.

- Reject direct `clnt_vc_create()`, `clnt_dg_create()`, `clntudp_create()`,
  `clnttcp_create()`, `clnt_create()` calls added outside these wrappers.
- **Every successful client needs `CLNT_DESTROY()` on every exit path**,
  including error returns added by the patch. The templates are
  `nfs_rpc_ping()` and `nfs_getport()` in `support/nfs/getport.c`.
- A patch that adds an early `return` between the `nfs_get_rpcclient()` and
  the `CLNT_DESTROY()` is a leak in a daemon and a finding.
- `rpc_createerr` is global. Code that calls a second RPC helper before
  reading `rpc_createerr.cf_stat` from the first has lost the error.

## rpcbind / portmap

`support/nfs/getport.c` speaks rpcbind v4 and v3, and portmap v2 (AF_INET
only). The version negotiation is a downward retry loop:

```c
for (rpcb_version = RPCBVERS_4; rpcb_version >= RPCBVERS_3; rpcb_version--)
```

falling back to `pmap_getport()` for AF_INET. Any new rpcbind procedure must
handle `RPC_PROGVERSMISMATCH`, `RPC_PROCUNAVAIL` and `RPC_PROGUNAVAIL` the
same way — an older rpcbind answering a v4 query must cause a v3 retry, not an
error to the caller.

Do not assume rpcbind is reachable at all. NFSv4 needs no rpcbind, and a
registration failure should warn and continue rather than abort. See
`netlink.md` for the userspace-rpcbind-registration path in `nfsdctl`.

## Server side

`support/nfs/rpcmisc.c` provides `rpc_init()`: the inetd-aware registration
path (`pmap_unset()`, `svcudp_create()`/`svctcp_create()`, `svc_register()`).
`support/nfs/svc_create.c` and `svc_socket.c` handle the TI-RPC transport
creation, including reserved-port binding.

Setup failures here use `xlog(L_FATAL, ...)`, which exits — appropriate at
startup, never in a request path.

**`my_svc_run()`.** `utils/statd/svc_run.c`, `utils/mountd/svc_run.c` and
`utils/exportd/` each carry a near-identical replacement for libc's
`svc_run()`, because they must interleave RPC dispatch with kernel cache
upcall servicing:

```c
/* select() on svc_fdset plus the cache channel fds */
svc_getreqset(&readfds);
cache_process(...);
```

These three copies drift. A fix to one is usually needed in the others —
check whether the patch updated all of them.

## AUTH handling

`nfs_authsys_create()` (`support/nfs/rpc_socket.c`) deliberately builds an
`AUTH_SYS` credential carrying **only the primary GID**, with a comment
explaining that AUTH_SYS cannot express more than 16 groups. This is used for
low-trust protocols such as MNT. Do not "fix" it to send the full group list.

Full-fidelity credential switching for privileged local work is a different
mechanism: `nfs_ucred_set_effective()` / `nfs_ucred_swap_effective()` in
`support/misc/ucred.c`, which sequence `setresgid()`/`setgroups()`/
`setresuid()` with explicit rollback labels on partial failure. Any change to
that ordering or to the rollback paths is security-sensitive — a partial
failure that does not roll back leaves the process with the wrong identity.

## rpcgen-generated code

`.x` files are the source of truth:

| IDL | Generated |
|---|---|
| `support/nsm/sm_inter.x` | `sm_inter_clnt.c`, `sm_inter_svc.c`, `sm_inter_xdr.c`, `sm_inter.h` |
| `support/export/mount.x` | `mount_clnt.c`, `mount_xdr.c`, `support/export/mount.h` |
| `tests/nsm_client/nlm_sm_inter.x` | `nlm_sm_inter_{clnt,svc,xdr}.c` |

- Never hand-edit the generated files. Change the `.x` and regenerate.
- Do not review generated files for style or for idiom compliance.
- `configure.ac` (`--with-rpcgen`) selects between the system `rpcgen` and the
  bundled `tools/rpcgen`, and applies different strict-prototype flags to
  each. A patch touching a `.x` file or the generation rules should be checked
  under both settings.

## XDR decoding of network input

XDR decode routines run on data from the network before any authentication
decision. When reviewing a change to a `xdr_*` routine or its callers:

- A decoded string or opaque array's length is attacker-controlled. Check it
  against the destination before copying.
- `xdr_string()` with a `maxsize` of `~0` accepts anything the transport
  delivered.
- Memory allocated by a decode must be released with `xdr_free()` on error
  paths, not just on success.
- A decode failure must be treated as a rejected request, not as an empty
  argument struct.

`rpc.statd` is the historical example of this going wrong; see `statd.md`.

## Cross-references

- `../../kernel/subsystem/sunrpc.md` — kernel-side transport, slot, and GSS
  invariants (when the kernel prompt set is installed).
- `statd.md` — the NSM service built on this machinery.
- `export.md` — the MOUNT service and the cache upcall loop that
  `my_svc_run()` drives.
