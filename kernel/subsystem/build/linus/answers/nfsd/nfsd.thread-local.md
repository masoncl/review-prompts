- `struct svc_rqst` has no rq_cachetype or rq_lease_breaker field in this
  tree; both live in `struct nfsd_thread_local_info` in `fs/nfsd/nfsd.h`, as
  `ntli_cachetype` and `ntli_lease_breaker`.
- `struct nfsd_thread_local_info` is not allocated: it is a zero-initialised
  local variable of `nfsd()` in `fs/nfsd/nfssvc.c`, so it lives on the thread's
  stack until `nfsd()` returns.
- `rq_private` in `struct svc_rqst` is a `void *` that `nfsd()` points at that
  variable once, before its request loop.
- `rq_private` is NULL in any `struct svc_rqst` not owned by an nfsd thread:
  `svc_prepare_thread()` zero-allocates and only `nfsd()` assigns the field.
- `ntli_cachetype`: `nfsd_dispatch()` rewrites it from `pc_cachetype` at the
  start of every request.
- `ntli_lease_breaker`: a `struct nfs4_client **`, set to `&cstate->clp` only
  in `nfsd4_proc_compound()`, after the minor-version and op-ordering checks.
- `ntli_lease_breaker` is never cleared: it is NULL until the thread's first
  such COMPOUND, and during NFSv2/v3 requests it still points into `rq_resp`.
- `nfsd_breaker_owns_lease()` in `fs/nfsd/nfs4state.c` dereferences it only
  after `nfsd_v4client()` on `nfsd_current_rqst()` succeeds.
- `nfsd4_deleg_getattr_conflict()` dereferences it with no test of its own;
  its one caller is in `fs/nfsd/nfs4xdr.c`.
