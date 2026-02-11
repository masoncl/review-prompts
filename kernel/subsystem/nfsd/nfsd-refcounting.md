# NFSD Reference Counting

Mismatched acquire/release calls on NFSD reference-counted objects cause
use-after-free, double-free, or resource leaks. The subsystem uses three
distinct refcounting APIs, and mixing up which API governs a given field
leads to silent corruption.

## refcount_t Objects (preferred for new code)

- `sc_count` on NFSv4 stateids (`struct nfs4_stid`) — managed via
  `refcount_set()`, `refcount_inc()`, `refcount_dec_and_test()`;
  see `nfs4_alloc_stid()` and `nfs4_put_stid()` in
  `fs/nfsd/nfs4state.c`.
- `fi_ref` on file objects (`struct nfs4_file`) — see
  `get_nfs4_file()` in `fs/nfsd/state.h` and `put_nfs4_file()` in
  `fs/nfsd/nfs4state.c`.
- `nf_ref` on file cache entries (`struct nfsd_file`) — see
  `nfsd_file_get()` and `nfsd_file_put()` in `fs/nfsd/filecache.c`.

## atomic_t Objects (legacy, still widely used)

- `se_ref` on sessions (`struct nfsd4_session`) — see
  `nfsd4_get_session_locked()` and `nfsd4_put_session_locked()` in
  `fs/nfsd/nfs4state.c`.
- `cl_rpc_users` on clients (`struct nfs4_client`) — see
  `get_client_locked()` and `put_client_renew_locked()` in
  `fs/nfsd/nfs4state.c`.
- `so_count` on state owners (`struct nfs4_stateowner`) — uses
  `atomic_dec_and_lock()` in `nfs4_put_stateowner()` to atomically
  drop the ref and acquire `cl_lock` for removal.
- `fi_access[2]` on file objects — tracks read vs write access counts;
  uses `atomic_dec_and_lock()` in `__nfs4_file_put_access()`.

## kref Objects

- `nbl_kref` on blocked locks (`struct nfsd4_blocked_lock`) — see
  `find_or_allocate_block()` and `free_blocked_lock()` in
  `fs/nfsd/nfs4state.c`.
- `cl_ref` on debugfs client refs (`struct nfsdfs_client`) — see
  `get_nfsdfs_client()` in `fs/nfsd/nfsctl.c` and `drop_client()` in
  `fs/nfsd/nfs4state.c`.

## Other Refcounting Patterns

- **cache_head-based**: `exp_get()` / `exp_put()` for exports in
  `fs/nfsd/export.h`; wraps `cache_get()` / `cache_put()`.
- **File handles**: `fh_copy()` / `fh_put()` in `fs/nfsd/nfsfh.c` —
  these manage dentry and export references but are not a simple
  refcount on the `svc_fh` itself.
- **Per-CPU refs**: `nfsd_net_try_get()` / `nfsd_net_put()` in
  `fs/nfsd/nfssvc.c` for namespace lifetime management.

## Early Assignment Bug Pattern

Assigning a reference-counted resource to a struct field before all
error checks complete creates leak or dangling-pointer bugs. If an
error path forgets to release the field (or releases it but leaves the
pointer set), subsequent cleanup may double-free or use-after-free.

```c
// WRONG — assignment before error check
obj->resource = get_resource();
if (error_condition) {
    put_resource(obj->resource);
    return error;  // field still points to freed object
}

// CORRECT — use temp variable
tmp = get_resource();
if (error_condition) {
    put_resource(tmp);
    return error;
}
obj->resource = tmp;  // assign only after all checks pass
```

**REPORT as bugs**: Code that assigns a newly acquired reference to a
struct field before all validation and error checks for the current
operation are complete.

## Quick Checks

- **Acquire/release balance**: every `*_get()`, `refcount_inc()`,
  `atomic_inc()`, or `kref_get()` must have a matching release on all
  paths (success and error).
- **Error path completeness**: verify all acquired references are
  released before returning an error.
- **dec_and_lock correctness**: when using `atomic_dec_and_lock()` or
  `atomic_dec_and_test()`, verify the lock or cleanup action matches
  what the destructor expects.
- **No double-free on error**: check whether a field already holds a
  value before the operation — releasing it again on error would
  double-free.
