| Reference | Taken | Dropped |
|---|---|---|
| Recall | `nfsd_break_one_deleg()`, with `refcount_inc_not_zero()` | `nfsd4_cb_recall_release()` |
| CB_GETATTR | `nfs4_cb_getattr()`, bare `refcount_inc()` | `nfsd4_cb_getattr_release()` |
| CB_NOTIFY | `nfsd4_run_cb_notify()`, with `refcount_inc_not_zero()` | `nfsd4_cb_notify_release()` |
| GETATTR conflict | `nfsd4_deleg_getattr_conflict()`, under `flc_lock` | itself, or its caller in `fs/nfsd/nfs4xdr.c` when `*pdp` is set |
| On `cl_revoked` | caller of `revoke_delegation()`, before unhash | `nfsd4_free_stateid()`, `nfsd4_drop_revoked_stid()`, `__destroy_client()` |

- `revoke_delegation()`: takes no reference; it consumes one through
  `destroy_unhashed_deleg()`, and the one left keeps the delegation on
  `cl_revoked`.
- Callers of `revoke_delegation()`: `nfs4_laundromat()` and
  `revoke_one_stid()` each do `refcount_inc()` before
  `unhash_delegation_locked()`.
- `sc_file`: the `struct nfs4_file` reference from `__alloc_init_deleg()`
  is put by the final `nfs4_put_stid()`, not by `destroy_unhashed_deleg()`.
- `fi_deleg_file`: counted separately by `fi_delegees`; `put_deleg_file()`
  releases the `struct nfsd_file` when it reaches 0.
- Lease owner: `nfs4_alloc_init_lease()` stores the delegation in
  `flc_owner` with no reference.
- **Unsafe usage**: dropping the in-force reference while the lease is
  still on `flc_lease`.
  - Unsafe: `nfsd_break_deleg_cb()` and `nfsd4_deleg_getattr_conflict()`
    dereference `flc_owner` under `flc_lock` with nothing else pinning it.
  - Safe: remove the lease, then put, as `destroy_unhashed_deleg()` does
    with `nfs4_unlock_deleg_lease()` before `nfs4_put_stid()`.
