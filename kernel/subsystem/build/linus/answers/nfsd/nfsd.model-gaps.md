- Models take an NFSv4 request to be deferrable on a cache miss once decoding
  has started. `nfs4svc_decode_compoundargs()` and `nfsd4_proc_compound()`
  clear `RQ_USEDEFERRAL`, and `svc_defer()` returns NULL without it.
- Models take the thread count to be fixed. Here, when `min_threads` in
  `struct nfsd_net` is non-zero, `nfsd()` in `fs/nfsd/nfssvc.c` spawns and
  retires threads. `nfsd_nrthreads()` reports the sum of every pool's ceiling
  `sp_nrthrmax`; `sp_nrthreads` is the running count.
- Models name no lock for the reclaim table. `reclaim_str_hashtbl` and
  `reclaim_str_hashtbl_size` are under the `rw_semaphore`
  `reclaim_str_hashtbl_lock`, not `client_lock`; outside the tracker's set-up
  and teardown, only the start-up read of the size in
  `nfs4_state_start_net()` is made without it.
  `nfsd4_find_reclaim_client()` takes no lock, its callers hold the
  semaphore.
- Models carry size limits from older trees, such as a 1 MB payload. Here
  `RPCSVC_MAXPAYLOAD` (`include/linux/sunrpc/svc.h`) and `NFSSVC_DEFBLKSIZE`
  are 4 MB, and `NFSD_MAX_OPS_PER_COMPOUND` is 200.
- Models take POSIX ACLs to reach clients only through NFSACL. Under
  `CONFIG_NFSD_V4_POSIX_ACLS`, NFSv4.2 also carries
  `FATTR4_WORD2_POSIX_ACCESS_ACL` and `FATTR4_WORD2_POSIX_DEFAULT_ACL`
  (`fs/nfsd/attr4.h`); `nfsd_setattr()` applies `na_pacl` and `na_dpacl`.
- Models know no fencing path for a layout whose lease break times out. Here
  `nfsd4_layout_lm_breaker_timedout()` in `fs/nfsd/nfs4layouts.c` pins the
  stateid and queues `ls_fence_work`; `nfsd4_layout_fence_worker()` retries
  `fence_client` with back-off.
- Models take NFSv2 and the recovery-directory backend to be always built.
  `CONFIG_NFSD_V2` and `CONFIG_NFSD_LEGACY_CLIENT_TRACKING` both default to n
  (`fs/nfsd/Kconfig`); without them `fs/nfsd/nfsproc.c` is not compiled and
  only the nfsdcld backends in `fs/nfsd/nfs4recover.c` remain.
