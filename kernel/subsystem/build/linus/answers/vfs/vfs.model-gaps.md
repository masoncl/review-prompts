- Models take `VFS_BUG_ON()`, `VFS_BUG_ON_INODE()` and `VFS_WARN_ON_ONCE()` to
  be checks that always run. Without `CONFIG_DEBUG_VFS` they compile to nothing
  (`include/linux/vfsdebug.h`), for example the occupied-slot check in
  `fd_install()`.
- Models take the syscall helpers that replaced do_unlinkat(), do_mkdirat()
  and do_renameat2() to consume the name. `filename_unlinkat()`,
  `filename_mkdirat()` and `filename_renameat2()` do not put the
  `struct filename`, the caller does (see the `CLASS(filename, ...)` users in
  `fs/namei.c`).
- Models take the delegated inode to be passed as a pointer to an inode pointer,
  and only to unlink, link and rename. It is `struct delegated_inode *`
  (`include/linux/filelock.h`), also taken by, for example, `vfs_create()`,
  `vfs_mkdir()`, `vfs_rmdir()` and `vfs_mknod()`, which call
  `try_break_deleg()` on the parent directory; `try_break_deleg()` takes a
  flags argument.
- Models take `->create` to take an excl flag. `->create` has four arguments.
  See `struct inode_operations` in `include/linux/fs.h`.
- Models take a NULL `->setlease` to mean the generic lease code is used.
  `kernel_setlease()` in `fs/locks.c` returns `-EINVAL` when the method is NULL.
- Models take `->update_time` and `->fileattr_set` at their older prototypes,
  and know only `->mmap`. `->update_time` takes `enum fs_update_time` and
  flags, `->fileattr_set` takes `struct file_kattr *`, and `->sync_lazytime`
  and `->mmap_prepare` exist; compare against `include/linux/fs.h`.
- Models take a filesystem to set sb->s_d_op directly and to call
  `d_set_d_op()`. The field is `__s_d_op`, set by `set_default_d_op()`;
  `d_set_d_op()` is static in `fs/dcache.c`.
- Models take `i_ino` and the inode-hash keys to be `unsigned long`. `i_ino` is
  `u64`, and `iget_locked()`, `ilookup()` and `iget5_locked()` take `u64`.
- Models write `f_path` freely. `f_path` is const and core code writes
  `__f_path`; `f_owner` is a pointer set up by `file_f_owner_allocate()`.
- Models take inode-state waiters to wait in wait_on_inode(). Waiters use
  `inode_bit_waitqueue()`, as `wait_on_new_inode()` does.
- Models miss that `setattr_prepare()` returns `-EPERM` for `ATTR_SIZE` on an
  `IS_VERITY()` inode.
