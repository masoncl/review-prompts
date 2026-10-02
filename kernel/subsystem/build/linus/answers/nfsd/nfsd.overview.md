- Global, not per-netns: `nfs4_file_rhltable` (`fs/nfsd/nfs4state.c`) and
  `nfsd_file_rhltable` (`fs/nfsd/filecache.c`) are single tables shared by
  every `struct nfsd_net`.
  - `struct nfsd_file`: carries `nf_net`, and `nfsd_file_lookup_locked()`
    filters on it.
  - `struct nfs4_file`: carries no netns; `nfsd4_file_hash_lookup()` makes no
    netns test.
- `struct nfs4_file`: hashed by inode pointer, then chosen by `fh_match()` on
  `fi_fhandle`; one inode can have several, marked `fi_aliased`.
- `struct nfsd_file`: hashed by inode pointer only; identity is then
  (`nf_may`, `nf_net`, cred, `NFSD_FILE_GC` bit), see
  `nfsd_file_lookup_locked()`.
  - A garbage-collected and a non-garbage-collected `struct nfsd_file` for
    the same file are different objects.
  - `nfsd_file_acquire_gc()`: used by the v2/v3 I/O paths; the other acquire
    variants (NFSv4 state, localio, directories) return non-GC objects.
- `struct nfsd_file_mark` on a directory: belongs to
  `nfsd_dir_fsnotify_group` and feeds `nfsd_handle_dir_event()`; it does not
  close files.
- `struct nfsd4_compound_state` (`fs/nfsd/xdr4.h`): the per-COMPOUND context;
  there is no nfsd4_compoundstate. It is embedded in
  `struct nfsd4_compoundres` as `cstate`.
- `struct svc_rqst`: one per nfsd kthread, reused for each RPC; see `nfsd()`
  in `fs/nfsd/nfssvc.c`.
- `struct svc_pool`: one per NUMA node that has CPUs, never per CPU; see
  `svc_pool_map_init_pernode()` in `net/sunrpc/svc.c`.
  - `sp_nrthrmin` and `sp_nrthrmax`: the pool's floor and ceiling; `nfsd()`
    retires a thread only while `sp_nrthreads` is above `sp_nrthrmin`, and
    spawns one only while it is below `sp_nrthrmax`.
- `struct nfsd4_copy` in the COMPOUND arguments: the transient COPY argument,
  not valid after the RPC.
- `sc_export` in `struct nfs4_stid`: open, lock, delegation and layout stids
  each hold a reference on the `struct svc_export` they were acquired
  through.
  - `drop_stid_export()` drops it early on admin revoke, so `sc_export` can
    be NULL on a live stid.
- `struct nfs4_delegation`: also represents a directory delegation, see
  `nfsd_get_dir_deleg()`.
  - `struct nfsd_notify_event`: one queued directory change awaiting
    CB_NOTIFY.
- `struct nfs4_layout_stateid`: holds its own reference on a
  `struct nfsd_file` (`ls_file`) and, unless the layout type sets
  `disable_recalls`, its own VFS lease, separate from `fi_fds` of the
  `struct nfs4_file`.
- Lock nesting, outermost first: `st_mutex`, then `deleg_lock`,
  `client_lock`, `cl_lock`, `fi_lock`.
  - Layout list linkage is under `cl_lock` and `fi_lock`, not `deleg_lock`.
- `struct svc_export` and `struct svc_expkey`: filled through netlink as well
  as the cache pipe; see `nfsd_cache_notify()` in `fs/nfsd/nfsctl.c` and
  `nfsd_nl_svc_export_set_reqs_doit()` in `fs/nfsd/export.c`.
- Localio: each `struct nfsd_file` handed to the NFS client by
  `nfsd_open_local_fh()` is paired with a reference on `nfsd_net_ref`;
  `nfsd_shutdown_net()`, when `NFSD_NET_UP` is set, kills that ref and waits
  for it to drain.
