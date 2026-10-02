- `nfsd4_lock_ol_stateid()`: tests `sc_status` only, through
  `nfsd4_verify_open_stid()`. It tests neither `sc_type` nor whether the
  stateid is still hashed.
- Return values: `nfserr_admin_revoked` for `SC_STATUS_ADMIN_REVOKED`,
  `nfserr_deleg_revoked` for `SC_STATUS_REVOKED`, `nfserr_bad_stateid` for
  `SC_STATUS_CLOSED`, tested in that order.
- Open stateid unhashed by `release_openowner()`: no `SC_STATUS_CLOSED` is
  set on it, so `nfsd4_lock_ol_stateid()` returns `nfs_ok`.
- Lock stateid: `unhash_lock_stateid()` sets `SC_STATUS_CLOSED` under
  `cl_lock` without that stateid's `st_mutex` (from
  `release_open_stateid_locks()` when the open stateid is closed), so holding
  `st_mutex` does not freeze a lock stateid's status.
- Lookup that allowed `SC_STATUS_CLOSED`, as `nfsd4_close()` does:
  `nfsd4_lock_ol_stateid()` still returns `nfserr_bad_stateid`, so
  `nfs4_seqid_op_checks()` never returns `nfs_ok` for a closed stateid; the
  mask only lets a v4.0 replay reach `nfserr_replay_me` from
  `nfsd4_check_seqid()`, before the mutex is taken.
- Lockdep subclass: `nfsd4_lock_ol_stateid()` always uses
  `LOCK_STATEID_MUTEX`, for open and lock stateids alike. A newly allocated
  stateid is locked with `OPEN_STATEID_MUTEX` in both `init_open_stateid()`
  and `init_lock_stateid()`.
- **Potentially unsafe usage**: linking state to a stateid once
  `nfsd4_lock_ol_stateid()` has returned `nfs_ok`.
  - Unsafe: when hashing was not rechecked; the stateid may be unhashed with
    `sc_status` still 0, and its `st_locks` is then not valid.
  - Safe: recheck `nfs4_ol_stateid_unhashed()` under `cl_lock` before
    linking, as `init_lock_stateid()` does for the open stateid.
