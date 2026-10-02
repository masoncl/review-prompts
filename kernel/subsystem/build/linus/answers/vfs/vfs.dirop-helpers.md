- `start_creating()`, `start_creating_killable()`, `start_creating_noperm()`
  on an existing name: return the positive dentry, not `-EEXIST`; they pass
  `LOOKUP_CREATE` without `LOOKUP_EXCL`.
- Positive dentry from `start_creating()`: the bracket is open and must be
  ended; `may_create_dentry()` in the `vfs_` helpers returns `-EEXIST` for
  it. `cachefiles_get_directory()` tests `d_is_negative()` and reuses a
  positive one.
- Exclusive creation: `simple_start_creating()` in `fs/libfs.c` and
  `start_creating_path()` pass `LOOKUP_CREATE | LOOKUP_EXCL` and return
  `ERR_PTR(-EEXIST)` for an existing name.
- `start_creating_dentry()` and `start_removing_dentry()`: do no lookup and no
  permission check; the checks they do make under the lock, and what they
  return, are in "Rechecking a dentry after locking".
- Write access: none of the forms that take a parent dentry calls
  `mnt_want_write()`; the caller does, as `ksmbd_vfs_kern_path_create()` does
  before `start_creating_noperm()`.
- `end_creating_keep()`: takes the one dentry, unlocks the parent, returns
  the same pointer with a reference the caller now owns; an `ERR_PTR` passes
  through untouched.
- `end_dirop()`: unlocks `de->d_parent->d_inode`, so the dentry passed to any
  end function must be the one whose parent was locked, or its replacement
  from `vfs_mkdir()`.
- `start_dirop()`: no name validation, no hashing, no permission check;
  declared in `fs/internal.h`; `end_dirop()` is exported and declared in
  `include/linux/fs.h`.
