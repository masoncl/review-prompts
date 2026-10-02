- may_delete(): not defined; the VFS checks are `may_create_dentry()` and
  `may_delete_dentry()` in `fs/namei.c`, both exported. `may_create()` in
  this tree is an unrelated static in `security/selinux/hooks.c`.
- `may_delete_dentry()` with a wrong parent: `BUG_ON(victim->d_parent->d_inode
  != dir)`, not an error return; a negative victim gives `-ENOENT` first.
- Trap checks: made inside the `start_renaming()` family (`-EINVAL` for a
  source that is an ancestor, `-ENOTEMPTY` or `-EINVAL` for a target that
  is); the caller never sees the trap dentry.
- `RENAME_NOREPLACE`: the `start_renaming()` family returns `-EEXIST` for a
  positive target itself.
- `vfs_rename()`: does not compare mounts and does not validate `flags`;
  `filename_renameat2()` does both before the call.
- Delegations: `vfs_create()`, `vfs_mknod()`, `vfs_mkdir()`, `vfs_symlink()`,
  `vfs_rmdir()`, `vfs_unlink()`, `vfs_link()` and `vfs_rename()` each take a
  `struct delegated_inode *` (`vfs_rename()` in `rd->delegated_inode`), and
  each calls `try_break_deleg()` on the parent directory; `vfs_unlink()`,
  `vfs_link()` and `vfs_rename()` also call it on a non-directory victim or
  source.
- `delegated_inode` NULL: allowed; `try_break_deleg()` can then still return
  `-EWOULDBLOCK`, without recording an inode to wait on.
- `vfs_create()`: takes idmap, dentry, mode and `struct delegated_inode *`;
  no directory inode, it uses `dentry->d_parent`; returns `-EACCES`, not
  `-EPERM`, when the filesystem has no `->create`.
