- `find_cpntf_state()`: tried by `nfs4_preprocess_stateid_op()` whenever
  `nfsd4_lookup_stateid()` returns `nfserr_bad_stateid`, whatever the caller
  passed. The stid it yields is the parent of the copy-notify state, looked
  up in the client named by `cp_p_clid`, which need not be `cstate->clp`.
- `nfsd4_stid_check_stateid_generation()`: also rechecks `sc_status` through
  `nfsd4_verify_open_stid()`, so a stateid closed or revoked since the lookup
  fails here.
- `*cstid`: receives the referenced stid on success when `cstid` is non-NULL;
  otherwise `nfs4_preprocess_stateid_op()` puts the reference itself.
- Special stateid: `*cstid` is not written. The caller initialises it to NULL
  and tests it; `nfsd4_copy_notify()` returns `nfserr_bad_stateid` for NULL.
- `*nfp`: filled by `nfs4_check_file()` only when `nfp` is non-NULL; set to
  NULL on entry.
- There is no nfs4_validate_open_stateid() in this tree, and
  `nfsd4_release_lockowner()` takes no stateid.

| Operation | Lookup | Checked for it | Checks itself |
|---|---|---|---|
| CLOSE, OPEN_CONFIRM, LOCKU, LOCK with a lock stateid | `nfs4_preprocess_seqid_op()` | seqid, `st_mutex` and status, generation, `nfs4_check_fh()` | open mode and confirmation are not checked by the helper |
| OPEN_DOWNGRADE, LOCK with an open stateid | `nfs4_preprocess_confirmed_seqid_op()` | the above plus `NFS4_OO_CONFIRMED` | `nfsd4_lock()` calls `nfs4_check_openmode()` and `same_clid()` |
| DELEGRETURN | `nfsd4_lookup_stateid()` | type and status | `fh_verify()`, `nfsd4_stid_check_stateid_generation()`, `nfs4_check_fh()` |
| OPEN claiming a delegation | `find_deleg_stateid()` in `nfs4_check_deleg()` | type; any status bit other than `SC_STATUS_REVOKED` fails the lookup | `SC_STATUS_REVOKED`, `nfs4_check_delegmode()`; no generation check; `nfsd4_process_open2()` compares `sc_file` |
| TEST_STATEID, FREE_STATEID | `find_stateid_locked()` under `cl_lock` | nothing | status and type; generation in TEST_STATEID, and in FREE_STATEID only for an open or lock stateid without `SC_STATUS_ADMIN_REVOKED` |
| LAYOUTGET, LAYOUTCOMMIT, LAYOUTRETURN | `nfsd4_preprocess_layout_stateid()` | `fh_match()`, takes `ls_mutex`; for an existing layout stateid also the layout type, and rejects only a generation newer than the server's | no further stateid check |
| OFFLOAD_STATUS, OFFLOAD_CANCEL | `find_async_copy_locked()` | whole-stateid match on `async_copies` | OFFLOAD_CANCEL falls back to `manage_cpntf_state()` |

- TEST_STATEID and FREE_STATEID: take no reference on the stid, except that
  `nfsd4_free_stateid()` takes one on a lock stateid before it drops
  `cl_lock`; they match on `so_id` alone in the session's client.
