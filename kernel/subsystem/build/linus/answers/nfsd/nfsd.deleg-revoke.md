- Lock: `nfs4_laundromat()` walks `nn->del_recall_lru` under
  `nn->deleg_lock`.
- What the laundromat can see: only delegations that
  `nfsd4_cb_recall_prepare()` put on `del_recall_lru`.
- Expired client: the laundromat skips the entry when `is_client_expired()`
  is true.
- Pinning: the laundromat bumps `cl_rpc_users` directly, not through
  `get_client_locked()`, until `revoke_delegation()` returns.
- `revoke_delegation()`: has no branch on `cl_minorversion`; only its
  `WARN_ON_ONCE()` reads it.
- NFSv4.0 from the laundromat: `unhash_delegation_locked()` stores
  `SC_STATUS_CLOSED` in place of `SC_STATUS_REVOKED`.
- NFSv4.0 in `revoke_delegation()`: the delegation is still added to
  `cl_revoked` with `SC_STATUS_FREEABLE`; the lease is removed and one
  reference remains.
- NFSv4.0 lookup: `find_stateid_by_type()` rejects `SC_STATUS_CLOSED`, so
  the client gets `nfserr_bad_stateid`.
- NFSv4.0 free: that delegation is freed when `__destroy_client()` drains
  `cl_revoked`.
- Comment in `fs/nfsd/state.h`: "destroyed (v4.0)" is not what
  `revoke_delegation()` does.
- NFSv4.0 admin revoke: the status stays `SC_STATUS_ADMIN_REVOKED`;
  `nfsd40_drop_revoked_stid()` drops it at first use,
  `nfs40_clean_admin_revoked()` later.
- `SC_STATUS_FREED`: already set when `nfsd4_free_stateid()` or
  `nfsd4_drop_revoked_stid()` ran first; `revoke_delegation()` then does not
  list the delegation.
- `SC_STATUS_FREEABLE`: tells `nfsd4_free_stateid()` that the delegation is
  on `cl_revoked` and must be unlinked.
- DELEGRETURN of a revoked stateid: `nfsd4_stid_check_stateid_generation()`
  returns `nfserr_deleg_revoked` before `destroy_delegation()` is reached;
  the delegation stays on `cl_revoked`.
- Final free: the last `nfs4_put_stid()` calls `sc_free`, which is
  `nfs4_free_deleg()`, or `nfs4_free_dir_deleg()` for a directory
  delegation.
