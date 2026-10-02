- `filename_create()`: static; it locks through `start_dirop()`.
- `start_creating()` family: declared in `include/linux/namei.h`; each locks
  the parent with `I_MUTEX_PARENT`. All but `start_creating_dentry()` and
  `start_removing_dentry()` do so in `__start_dirop()` and look the name up.
- nfsd, cachefiles, overlayfs, ecryptfs, ksmbd and devtmpfs: use that family;
  none locks a parent itself to create, remove or rename an entry.
- By-hand examples: `fuse_reverse_inval_entry()` in `fs/fuse/dir.c` and
  `bm_remove_entry()` in `fs/binfmt_misc.c`.
- **Potentially unsafe usage**: plain `inode_lock()` on a parent directory.
  - Unsafe: when `vfs_rmdir()`, `vfs_unlink()` or `vfs_link()` follows; each
    calls `inode_lock()` on the victim or the link source, and
    `check_deadlock()` reports recursion if the two share a lock key.
  - Safe: when no second `i_rwsem` of that key is taken under it, as in
    `lookup_open()`.
  - Safe: `inode_lock_nested(dir, I_MUTEX_PARENT)` then `inode_lock()` on the
    child, as `fuse_reverse_inval_entry()` does.
- **Potentially unsafe usage**: holding `i_rwsem` on two directories.
  - Unsafe: when both are on one filesystem, neither is the parent of the
    other and `s_vfs_rename_mutex` is not held; `lock_two_directories()`
    orders by ancestry and can take them in the opposite order.
  - Safe: parent then its child, as `cachefiles_get_directory()` does after
    `start_creating()`.
  - Safe: through `start_renaming()` and its variants.
  - Safe: a directory of a stacking filesystem, then one of the filesystem
    below it, as `ecryptfs_do_unlink()` does under `->unlink`;
    `lock_two_directories()` returns `-EXDEV` without locking when the two
    share no ancestor.
