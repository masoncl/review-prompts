- `devcgroup_inode_permission()`: runs after `do_inode_permission()` and before
  `security_inode_permission()`; returns 0 at once unless the inode is a block
  or char device with a non-zero `i_rdev`; a stub that returns 0 when neither
  `CONFIG_CGROUP_DEVICE` nor `CONFIG_CGROUP_BPF` is set.
- Mount read-only state: not tested anywhere in `inode_permission()`;
  `sb_permission()` looks only at `sb_rdonly()`, so the caller still needs
  `mnt_want_write()`, as `vfs_truncate()` does after its `inode_permission()`.
- New test in `sb_permission()` or `inode_permission()` that applies without
  `MAY_WRITE`: `lookup_inode_permission_may_exec()` bypasses it on its fast
  path and has to be changed too.
- `IOP_FASTPERM_MAY_EXEC`: set by a filesystem on directories that have a
  `->permission` method, to let path lookup skip that method; the method must
  then add nothing for `MAY_EXEC` on a directory. Set only in
  `fs/btrfs/inode.c`.
- **Potentially unsafe usage**: calling only `security_inode_permission()`.
  - Unsafe: when the mask can hold `MAY_WRITE`, the inode can be a device
    node, or the mode bits, ACL or `->permission` method could deny; the
    `-EROFS`, `-EPERM`, `-EACCES` and device cgroup results are never produced.
  - Safe: mask is `MAY_EXEC` with at most `MAY_NOT_BLOCK`, the inode is a
    directory with `IOP_FASTPERM` or `IOP_FASTPERM_MAY_EXEC`, all of mode
    `0111` is set and `no_acl_inode()` is true, as in
    `lookup_inode_permission_may_exec()`; `acl_permission_check()` returns 0
    for the same condition.
- **Potentially unsafe usage**: calling `generic_permission()` directly.
  - Unsafe: as the whole access decision; everything in `inode_permission()`
    outside `do_inode_permission()` is skipped, including the LSM hook.
  - Safe: inside a `->permission` method, which `do_inode_permission()` calls
    from within the chain, as `btrfs_permission()` does.
