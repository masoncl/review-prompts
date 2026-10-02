- `->tmpfile`: called with no `i_rwsem` held; `vfs_tmpfile()` in `fs/namei.c`
  locks nothing on the directory.
- `->lookup`: the parent is held shared from `lookup_slow()`, exclusive from
  `lookup_one_qstr_excl()` and from `lookup_open()` when `O_CREAT` is set.
- `lookup_one()` and `lookup_noperm()`: call `->lookup` under whichever mode
  the caller holds; they only `WARN_ON_ONCE()` when the lock is not held.
- `->atomic_open`: the `open_flag` argument does not tell the lock mode.
  `lookup_open()` picks the mode from `op->open_flag`, then clears `O_CREAT`
  from the value it passes on when `create_error` is set, so the method can
  see no `O_CREAT` with the parent held exclusive.
- `dentry_create()`: also calls `->atomic_open`, under a parent lock that its
  caller took.
- `->fileattr_get`: `vfs_fileattr_get()` takes no lock; `vfs_fileattr_set()`
  calls it with the inode held exclusive.
- `->rename`: both parents are exclusive; the children that `vfs_rename()`
  locks are:

| Child | Locked by `vfs_rename()` |
|---|---|
| non-directory source | always |
| directory source | only when the parents differ |
| non-directory target that exists | always |
| directory target | unless the parents are equal and `RENAME_EXCHANGE` is set |
