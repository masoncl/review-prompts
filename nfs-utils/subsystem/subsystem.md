# nfs-utils Subsystem Guide Index

Load subsystem guides based on what the patch touches. Each guide holds
component-specific invariants, API contracts, and known bug patterns.

A change can match multiple rows. Load **every** matching guide, not just the
most specific one. A patch adding a netlink command to `exportfs` matches both
the Netlink and the Export rows.

> **Path resolution:** every filename in the File column is relative to this
> file's directory, `review-prompts/nfs-utils/subsystem/`.

## Guides

| Subsystem | Triggers | File |
|---|---|---|
| SunRPC / libtirpc | `utils/showmount/`, `support/nfs/{rpc_socket,getport,rpcmisc,rpcdispatch,svc_socket,svc_create}.c`, `support/export/mount_{clnt,xdr}.c`, `support/nsm/{rpc,sm_inter_*}.c`, `CLIENT *`, `clnt_`, `svc_`, `AUTH_`, `rpcb_`, `pmap_`, `xdr_`, `*.x`, `HAVE_LIBTIRPC` | sunrpc.md |
| Netlink | `utils/nfsdctl/`, `support/nfs/nfsdnl.c`, `support/include/{nfsd,lockd,sunrpc}_netlink.h`, `utils/nfsstat/`, `nla_`, `nl_`, `genl`, `NFSD_A_`, `NFSD_CMD_`, `SUNRPC_CMD_`, `HAVE_NFSD_NETLINK` | netlink.md |
| Export / mountd | `utils/{exportfs,mountd,exportd,showmount}/`, `support/export/`, `support/misc/nfsd_path.c`, `support/nfs/{exports,rmtab,cacheio}.c`, etab, rmtab, xtab, `qword_`, `/etc/exports` | export.md |
| NSM / statd | `utils/statd/`, `support/nsm/`, `sm-notify`, `SM_MON`, `SM_NOTIFY`, `/var/lib/nfs/sm` | statd.md |
| Upcall daemons | `utils/{gssd,idmapd,nfsdcld,nfsdcltrack,blkmapd}/`, `support/nfsidmap/`, `rpc_pipefs`, inotify, libevent, `gss_`, `krb5`, sqlite | upcalls.md |
| Mount helper | `utils/mount/`, `mount.nfs`, `umount.nfs`, `CONFIG_LIBMOUNT`, `MOUNT_CONFIG`, `nfsmount.conf`, option/device string parsing | mount.md |
| nfs.conf | `support/nfs/conffile.c`, `support/include/conffile.h`, `tools/nfsconf/`, `conf_get_`, `conf_init_`, `nfs.conf` | config.md |
| Build / packaging | `configure.ac`, `Makefile.am`, `aclocal/`, `systemd/`, `tools/*/*.py`, `tests/`, `HAVE_*`, `CONFIG_*`, `ENABLE_*` | build.md |

## Cross-Tree References

When a patch pairs with a kernel-side change, the kernel invariants live in
the kernel prompt set (installed separately):

- `../../kernel/subsystem/nfsd.md` — nfsd file layout, trust boundaries, XDR
  codec, file handle and stateid lifecycles, the nfsd netlink interface,
  re-export.
- `../../kernel/subsystem/sunrpc.md` — SunRPC client and server transport
  invariants, GSS patterns.

These are useful context for "does the userspace side match what the kernel
actually does", especially for `nfsdctl` netlink work and export cache upcalls.
Do not assume they are installed; skip the reference if the files are absent.

## Not Covered by a Guide

Components without a dedicated guide, and where to look instead:

- `utils/nfsd/` (`rpc.nfsd`) — a control tool that writes `/proc/fs/nfsd/*`
  and, on newer kernels, drives netlink. Use `netlink.md` plus
  `technical-patterns.md`.
- `utils/nfsref/`, `support/junction/` — RFC 5716 junctions, libxml2-backed,
  gated by `CONFIG_JUNCTION`. Use `export.md` for the export-side interaction
  and `build.md` for the gating.
- `support/reexport/` (`fsidd`) — a libevent daemon on a `AF_UNIX` socket with
  a sqlite backend. Use `technical-patterns.md` daemon rules plus `upcalls.md`
  for the sqlite conventions.
- `systemd/*generator*.c` — systemd generators run very early with high trust.
  Review them with the same care as setuid code; see `build.md`.
