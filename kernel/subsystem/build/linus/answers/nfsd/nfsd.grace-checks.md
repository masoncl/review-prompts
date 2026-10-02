- `opens_in_grace()` and `locks_in_grace()` in `fs/nfs_common/grace.c`: take
  only a `struct net *`; the caller compares the claim type or reclaim flag.
- `opens_in_grace()`: true only while a manager with `block_opens` set is on
  the list; `locks_in_grace()`: true while any manager is, lockd's included.
- There is no nfsd4_in_grace() here.
- `nfsd4_process_open1()` and `nfs4_check_open_reclaim()`: call neither
  helper; the open test is in `nfsd4_open()` in `fs/nfsd/nfs4proc.c`, after
  `nfsd4_process_open1()`.
- `nn->client_lock`: not held at the grace tests in `nfsd4_open()` or
  `nfsd4_lock()`.
- `nfsd4_reclaim_complete()`: calls neither helper, so it is not an example of
  the pattern.
- `nfsd4_open()`, sessions pre-check: a non-`NFS4_OPEN_CLAIM_PREVIOUS` open
  from a client without `NFSD4_CLIENT_RECLAIM_COMPLETE` gets `nfserr_grace`
  whatever `opens_in_grace()` says, so also after grace has ended.
- `NFS4_OPEN_CLAIM_PREVIOUS` during grace: can still fail in
  `nfs4_check_open_reclaim()`, with `nfserr_no_grace` if
  `NFSD4_CLIENT_RECLAIM_COMPLETE` is set, else `nfserr_reclaim_bad` if
  `nfsd4_client_record_check()` fails.
- `nfsd4_client_record_check()`: returns `-EOPNOTSUPP` when
  `nn->client_tracking_ops` is `NULL`, so every reclaim open that reaches it
  then gets `nfserr_reclaim_bad`.
- `nfsd4_lock()` has a third test after the pair: a reclaim lock from a client
  with `NFSD4_CLIENT_RECLAIM_COMPLETE` set gets `nfserr_no_grace` during grace.
- `nfsd4_layoutcommit()` (under `CONFIG_NFSD_PNFS`): a third two-sided
  example, `locks_in_grace()` against `lcp->lc_reclaim`.
- One-sided `nfserr_grace` checks: search `fs/nfsd` for the two helper names;
  members easy to miss are `nfsd4_setxattr()`, `nfsd4_removexattr()` and
  `nfsd4_block_proc_layoutget()`.
- There is no grace_disallows_io() here; `check_special_stateids()` in
  `fs/nfsd/nfs4state.c` does that job with `opens_in_grace()`.
- `check_special_stateids()`: a read with the all-ones stateid
  (`ONE_STATEID()` with `RD_STATE`) returns `nfs_ok` during grace; the other
  special-stateid cases get `nfserr_grace`.
- `nlmsvc_lock()` in `fs/lockd/svclock.c`: returns
  `nlm_lck_denied_grace_period` in both directions, also for a reclaim outside
  grace.
- **Potentially unsafe usage**: testing only the in-grace direction (helper
  true, return `nfserr_grace`).
  - Unsafe: in an NFSv4 operation whose arguments carry a reclaim flag or
    claim type; a reclaim sent after grace is then not refused with
    `nfserr_no_grace`.
  - Safe: in an operation with no reclaim form, as `nfsd4_lockt()`,
    `nfsd4_remove()` and `nfsd4_rename()` do; the paired tests in
    `nfsd4_open()` and `nfsd4_lock()` define the two-sided form.
