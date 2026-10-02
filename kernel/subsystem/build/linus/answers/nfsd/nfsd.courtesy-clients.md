- `NFSD4_ACTIVE` to `NFSD4_COURTESY`: `nfs4_get_client_reaplist()` does it for
  every client whose lease has run out and whose `cl_rpc_users` is 0. No other
  condition.
- What happens next in the same pass: the client is expired at once if it has
  no state, if `nfs4_anylock_blockers()` is true, or if the client count is
  at `nn->nfs4_max_clients` and fewer than `NFSD_CLIENT_MAX_TRIM_PER_RUN`
  were reaped. Otherwise it stays `NFSD4_COURTESY`.
- `nfs4_anylock_blockers()`: also true when `cl_delegs_in_recall` is
  non-zero.
- `NFSD4_EXPIRABLE`: tested before the lease test; the client goes straight
  to `mark_client_expired_locked()`, past the state and blocker tests.
- `NFSD_COURTESY_CLIENT_TIMEOUT`: defined in `fs/nfsd/nfsd.h`, used nowhere.
  No code limits how long a client stays `NFSD4_COURTESY`.
- Back to `NFSD4_ACTIVE`: `get_client_locked()` and `renew_client_locked()`
  both set it, from either state, while `cl_time` is not 0.
- Who reaches those two, for example: SEQUENCE through
  `nfsd4_get_session_locked()`; any clientid lookup through
  `find_client_in_id_table()`; the last `put_client_renew()`.
- `nfsd4_client_record_check()`: does not change `cl_state`.
- Counter: `nn->nfsd_courtesy_clients`. nfs4_courtesy_client_count is not in
  this tree.
- Lock manager callbacks: `nfsd4_lm_lock_expirable()` and
  `nfsd4_lm_expire_lock()`, in `nfsd_posix_mng_ops`.
- Callers of the lock manager callbacks: `posix_lock_inode()` and
  `posix_test_lock()` in `fs/locks.c`.
- `nfsd4_lm_lock_expirable()`: runs under `flc_lock`, so it must not sleep.
  `nfsd4_lm_expire_lock()` runs after `flc_lock` is dropped and flushes
  `laundry_wq`.
