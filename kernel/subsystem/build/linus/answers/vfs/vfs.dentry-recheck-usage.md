- Checks under the lock, as `start_removing_dentry()` and
  `start_creating_dentry()` in `fs/namei.c` make them:
  `!IS_DEADDIR(parent->d_inode)`, `child->d_parent == parent`,
  `!d_unhashed(child)`, then positive for removal or negative for creation.
- Error codes: `-EINVAL` when one of the first three fails; then `-ENOENT`
  from `start_removing_dentry()` for a negative child, `-EEXIST` from
  `start_creating_dentry()` for a positive one; the parent is unlocked on
  each.
- Reference: the helper returns `dget(child)`; the end function drops that
  one, the caller's own reference stays.
- Rename helpers: test `d_unhashed()` and the parent of a passed dentry, not
  that the source is positive or that its parent is dead;
  `may_delete_dentry()` in `vfs_rename()` tests those.
- lock_parent(), fh_lock() and ovl_parent_lock(): not defined in this tree.
- **Unsafe usage**: locking a directory taken from a held dentry, then
  passing the dentry to a `vfs_` helper or an end function with no recheck.
  - Unsafe: when another task can rename or remove the entry before the lock
    is taken; `may_delete_dentry()` hits its `BUG_ON()`, `vfs_create()` works
    on `dentry->d_parent`, and `end_dirop()` unlocks
    `de->d_parent->d_inode`, each of which may be an unlocked directory.
  - Safe: `start_removing_dentry()`, as in `cachefiles_delete_object()`,
    `ovl_cleanup()` and `ksmbd_vfs_unlink()`; the last takes the parent with
    `dget_parent()` first.
  - Safe: `start_creating_dentry()`, as in `ecryptfs_start_creating_dentry()`.
  - Safe: `start_renaming_dentry()`, as in `ksmbd_vfs_rename()` and
    `cachefiles_bury_object()`.
  - Safe: looking the name up under the lock instead, with
    `start_removing()` or `start_removing_path()`, as `handle_remove()` in
    `drivers/base/devtmpfs.c` does.
