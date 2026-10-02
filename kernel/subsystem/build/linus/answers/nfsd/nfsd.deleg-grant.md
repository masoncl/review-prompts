- Locks at hashing: `nn->deleg_lock`, then `clp->cl_lock`, then
  `fp->fi_lock`; `hash_delegation_locked()` asserts all three.
- Early check: `nfs4_delegation_exists()` and the `fi_delegees` update run
  under `nn->deleg_lock` and `fp->fi_lock` only.
- Callback channel: `nfsd4_cb_channel_good()` accepts `NFSD4_CB_UP`, and also
  `NFSD4_CB_UNKNOWN` when `cl_minorversion` is not 0.
- `NFS4_OPEN_CLAIM_PREVIOUS` in `nfs4_open_delegation()`: always goes on to
  `nfs4_set_delegation()`; the grace, callback-up and `NFS4_OO_CONFIRMED`
  tests are not applied to it.
- `op_delegate_type` from the request: `nfs4_open_delegation()` never reads
  it.
- `NFS4_OPEN_CLAIM_NULL` and `NFS4_OPEN_CLAIM_FH`: an open with
  `NFS4_SHARE_ACCESS_WRITE` from a `cl_minorversion` 0 client gets no
  delegation.
- Kind: `OPEN_DELEGATE_WRITE` when `op_share_access` has
  `NFS4_SHARE_ACCESS_WRITE` and `find_writeable_file()` finds a file;
  otherwise `OPEN_DELEGATE_READ` when it has `NFS4_SHARE_ACCESS_READ`.
- ATTRS_DELEG forms: `OPEN_DELEGATE_WRITE_ATTRS_DELEG` or
  `OPEN_DELEGATE_READ_ATTRS_DELEG` replaces the plain kind in `dl_type` when
  `nfsd4_want_deleg_timestamps()` is true.
- `nfsd4_want_deleg_timestamps()`: needs `nfsd_delegts_enabled` and
  `OPEN4_SHARE_ACCESS_WANT_DELEG_TIMESTAMPS`.
- Want flags: `OPEN4_SHARE_ACCESS_WANT_READ_DELEG` and
  `OPEN4_SHARE_ACCESS_WANT_WRITE_DELEG` do not choose the kind.
- Other openers: there is no credential test and no "sole opener" test;
  `nfsd4_check_conflicting_opens()` rejects only other writers, for both
  kinds.
- Other leases: `generic_add_lease()` returns `-EAGAIN` for `F_WRLCK` when
  any other lease is on the file, so a write delegation is not granted while
  another client's delegation is on the file.
- Lease call: `kernel_setlease()`, not `vfs_setlease()`.
- Global switch: there is no NFSD delegation-enable variable;
  `leases_enable` in `fs/locks.c`, when 0, makes `generic_add_lease()`
  return `-EINVAL`.
