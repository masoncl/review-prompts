- `nfsd4_lookup_stateid()`: adds `SC_STATUS_ADMIN_REVOKED` and
  `SC_STATUS_FREEABLE` to the status mask on every call.
- `SC_STATUS_REVOKED`: added to the mask when the type mask has
  `SC_TYPE_DELEG`.
- `SC_STATUS_REVOKED` found, caller's mask lacked it: `nfserr_deleg_revoked`.
  This test comes first.
- `SC_STATUS_ADMIN_REVOKED` found: `nfserr_admin_revoked`, even when the
  caller's mask had the bit; such a stateid is never returned.
- `SC_STATUS_FREEABLE`: maps to no error; it is let through so that a revoked
  delegation on `cl_revoked` reaches the two tests above.
- `SC_STATUS_CLOSED` and `SC_STATUS_FREED`: never forced; a stateid with
  either gives `nfserr_bad_stateid` unless the caller's mask has the bit.
- In-tree masks: `nfsd4_close()` passes `SC_STATUS_CLOSED`, through
  `nfs4_preprocess_seqid_op()`; `nfsd4_delegreturn()` passes
  `SC_STATUS_REVOKED`; every other caller passes 0.
- Never returned: a stateid for which `ZERO_STATEID()`, `ONE_STATEID()` or
  `CLOSE_STATEID()` is true; a stid of type `SC_TYPE_COPY`.
- `so_clid` differs from `cstate->clp`: `set_client()` fails, giving
  `nfserr_bad_stateid` with a session and `nfserr_stale_stateid` without.
- v4.0 client not found by `set_client()`: `nfserr_expired`, passed through.
- `find_stateid_by_type()`: takes the reference with `refcount_inc()` under
  `cl_lock`; it does not call `refcount_inc_not_zero()`.
