- should_remove_suid() does not exist here; callers compute the kill flags
  with `setattr_should_drop_suidgid()` (through `dentry_needs_remove_privs()`
  in `do_truncate()`) or `setattr_should_drop_sgid()` (in `chown_common()`).
- `notify_change()` and the kill flags: it does not call
  `setattr_should_drop_suidgid()`; it tests `S_ISUID` and `S_ISGID` in
  `inode->i_mode` and builds `ATTR_MODE` with `ia_mode` from them.
- `ATTR_MODE` together with `ATTR_KILL_SUID` or `ATTR_KILL_SGID`: `BUG()`.
- `ATTR_MODE` on a symlink: `-EOPNOTSUPP`, tested right after
  `may_setattr()`.
- `S_IALLUGO` masking: done by `chmod_common()` in `fs/open.c`;
  `notify_change()` passes `ia_mode` on as given.
- Time fields: `notify_change()` sets no `ATTR_*` time flag; it overwrites
  `ia_atime`, `ia_mtime` and `ia_ctime` with `current_time()`, except a field
  whose `ATTR_ATIME_SET`, `ATTR_MTIME_SET` or `ATTR_CTIME_SET` is set, which
  it passes through `timestamp_truncate()`.
- `ATTR_DELEG`: with it `notify_change()` skips `try_break_deleg()`; nfsd sets
  it for updates from a delegation holder.
- `may_setattr()`: its owner test is for `ATTR_TOUCH` only, with
  `inode_permission()` and `MAY_WRITE` as the fallback; the
  `inode_owner_or_capable()` test for explicit times is in
  `setattr_prepare()`.
- Unmapped-owner tests (`-EOVERFLOW`): run after the early `return 0` for an
  `ia_valid` holding only kill flags, and before `security_inode_setattr()`.
- Mount write access: `notify_change()` does not test it; `chmod_common()`
  takes `mnt_want_write()` itself, `chown_common()` relies on its caller, for
  example `do_fchownat()`.
- `delegated_inode`: a `struct delegated_inode *`, tested afterwards with
  `is_delegated()`; `NULL` is accepted, as `do_truncate()` passes, and then
  `-EWOULDBLOCK` comes back with nothing to wait on.
- Quota step in `->setattr`: `is_quota_modification()` gates
  `dquot_initialize()`; `dquot_transfer()` is gated by `i_uid_needs_update()`
  or `i_gid_needs_update()`; see `ext2_setattr()`.
- `setattr_copy()` on an `is_mgtime()` inode: ignores `ia_ctime` unless
  `ATTR_CTIME_SET`; with `ATTR_CTIME` it takes the ctime from
  `inode_set_ctime_current()`; see `setattr_copy_mgtime()` in `fs/attr.c`.
