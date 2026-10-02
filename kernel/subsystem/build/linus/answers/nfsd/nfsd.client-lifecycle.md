- `force_expire_client()`: zeroes `cl_time` itself under `client_lock`, while
  the client is still hashed, then sleeps until `cl_rpc_users` is 0. It does
  not call `mark_client_expired_locked()`, so nothing refuses it.
- `client_has_state()`: also counts `cl_sessions` and running async copies
  (`nfsd4_has_active_async_copies()`).
- `client_has_state()` as a refusal: on its own only in
  `nfsd4_destroy_clientid()`. `nfsd4_exchange_id()` and
  `nfsd4_setclientid_confirm()` refuse with `nfserr_clid_inuse` only when the
  credentials also differ; `nfsd4_setclientid()` also when
  `clp_used_exchangeid()` is true.
- EXCHANGE_ID with a new verifier and the same credentials: leaves the
  confirmed client alone, with or without state. The CREATE_SESSION that
  confirms the new record replaces it with no `client_has_state()` test;
  `mark_client_expired_locked()` can still refuse.
- `__destroy_client()` precondition: the client is already unhashed; both
  callers run `unhash_client()` first.
- `__destroy_client()` order:
  1. under `deleg_lock` of `struct nfsd_net`: `unhash_delegation_locked()` on
     every entry of `cl_delegations`;
  2. `destroy_unhashed_deleg()` on each, lock dropped;
  3. `nfs4_put_stid()` on every entry of `cl_revoked`;
  4. `release_openowner()` on every entry of `cl_openowners`;
  5. each lockowner left in `cl_ownerstr_hashtbl`:
     `unhash_lockowner_locked()`, `remove_blocked_locks()`,
     `nfs4_put_stateowner()`;
  6. `nfsd4_return_all_client_layouts()`;
  7. `nfsd4_shutdown_copy()`;
  8. `nfsd4_shutdown_callback()`;
  9. put `cl_cb_conn.cb_xprt`, decrement `nn->nfs4_client_count` and the
     courtesy count; under `CONFIG_NFSD_SCSILAYOUT`, `xa_destroy()` of
     `cl_dev_fences`;
  10. `free_client()`: frees sessions, removes the nfsdfs directory, calls
      `nfsd4_put_client()`;
  11. `wake_up_all(&expiry_wq)`.
- `nfsd4_async_copy_reaper()`: called from `nfs4_laundromat()`, not from
  `__destroy_client()`.
