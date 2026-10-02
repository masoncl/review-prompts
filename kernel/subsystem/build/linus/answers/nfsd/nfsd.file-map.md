| Job | File | Easy to miss |
|---|---|---|
| Netlink, hand-written | `fs/nfsd/nfsctl.c` and `fs/nfsd/export.c` | `fs/nfsd/export.c` defines `nfsd_nl_svc_export_get_reqs_dumpit()`, `nfsd_nl_svc_export_set_reqs_doit()`, `nfsd_nl_expkey_get_reqs_dumpit()` and `nfsd_nl_expkey_set_reqs_doit()`; every other handler declared in `fs/nfsd/netlink.h`, and the multicast sender `nfsd_cache_notify()`, is in `fs/nfsd/nfsctl.c` |
| Generated XDR | `fs/nfsd/nfs4xdr_gen.c`, `fs/nfsd/nfs4xdr_gen.h` | generated from `Documentation/sunrpc/xdr/nfs4_1.x` by the `xdrgen` target in `fs/nfsd/Makefile`, which also writes the types to `include/linux/sunrpc/xdrgen/nfs4_1.h`; covers only some NFSv4 types, called from the hand-written `fs/nfsd/nfs4xdr.c` and `fs/nfsd/nfs4callback.c` |
| debugfs | `fs/nfsd/debugfs.c` | built only with `CONFIG_DEBUG_FS`; no other file under `fs/nfsd/` creates debugfs entries, `fs/nfsd/nfsctl.c` only calls `nfsd_debugfs_init()` and `nfsd_debugfs_exit()` |
