- `put_client_no_renew()` and `put_client_no_renew_locked()`: defined in
  `fs/nfsd/nfs4state.c`, next to `put_client_renew()`.
- Difference: on the last put of a client that is not expired,
  `put_client_renew()` calls `renew_client_locked()`; `put_client_no_renew()`
  does nothing.
- On an expired client: the last put of either form only wakes `expiry_wq`.
- Callers of the no-renew form: work the server starts itself.
  `nfsd4_revoke_states()`, `nfsd4_revoke_export_states()`,
  `nfs40_clean_admin_revoked()`, and three loops in `nfs4_laundromat()`
  (timed-out delegations, `close_lru`, blocked locks).
- The matching pin: `atomic_inc()` of `cl_rpc_users` under `client_lock`,
  after `is_client_expired()` returned false. Not `get_client_locked()`, which
  sets `NFSD4_ACTIVE`.
- **Unsafe usage**: pinning a client for server-initiated work with
  `get_client_locked()`, or releasing that pin with `put_client_renew()`.
  - Unsafe: `get_client_locked()` makes a courtesy client `NFSD4_ACTIVE`; the
    last `put_client_renew()` does the same and renews the lease.
  - Safe: bare `atomic_inc()` then `put_client_no_renew()`, as
    `nfs4_laundromat()` does.
  - Safe: `put_client_renew()` at the end of the client's own request, as
    `nfsd4_sequence_done()` does.
