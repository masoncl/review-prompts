- `struct inode` holds no reference on its superblock, active or passive.
  `generic_shutdown_super()` evicts the inodes with a zero count with
  `evict_inodes()`; any inode still on `s_inodes` afterwards is reported as
  "Busy inodes" and has `i_sb` poisoned, or is a `BUG()` under
  `CONFIG_BUG_ON_DATA_CORRUPTION`.
- `struct mount`: defined in `fs/mount.h` and used across `fs/`, for example
  `fs/namei.c` and `fs/d_path.c`, not only `fs/namespace.c` and `fs/pnode.c`.
- `struct mountpoint`: in `fs/mount.h`, with no reference count. It holds a
  reference on its dentry and lives while `m_list` is non-empty; `m_list`
  links the mounts on that dentry and any `struct pinned_mountpoint`.
- `struct mnt_namespace`: not always what a task sees. One with `is_anon` set
  holds a detached tree. A mount's `mnt_ns` can also be NULL or
  `MNT_NS_INTERNAL`. Mounts of a namespace are in the rbtree `mounts`, keyed
  by `mnt_id_unique`.
- Namespace root: `init_mount_tree()` makes a `nullfs_fs_type` mount
  (`fs/nullfs.c`, empty and immutable) the root of the initial namespace and
  mounts the rootfs on top of it. The visible root of a namespace is
  `topmost_overmount()` of its `root`, not `root` itself; see
  `current_chrooted()`.
- `struct file` `f_inode`: always set from `f_path.dentry->d_inode`, in
  `do_dentry_open()` and `file_init_path()`; `file_dentry()` warns if the two
  differ.
- Stacking filesystems such as overlayfs: a second `struct file`, embedded in
  `struct backing_file` (`fs/file_table.c`, `FMODE_BACKING`), has both
  `f_path` and `f_inode` on the underlying filesystem. The path the user
  opened is kept beside it; read it with `file_user_path()`.
- `struct address_space` of a block device: `bdev_open()` in `block/bdev.c`
  redirects the file's `f_mapping`; the device node's `i_mapping` is left
  alone. `i_mapping` is repointed elsewhere, for example in
  `drivers/dax/device.c`.
- `struct dentry` parent chain: ends at an `IS_ROOT()` dentry, which need not
  be `s_root`. `d_obtain_alias()` makes disconnected roots, and
  `d_obtain_root()` makes secondary roots listed on `s_roots`.
- Directory aliases: a directory inode has at most one.
  `d_splice_alias_ops()` moves the existing alias, hashed or not, into place
  or fails with `-ELOOP` or `-ESTALE`; `d_obtain_alias()` returns the existing
  one.
- `struct super_dev` (`fs/super.c`): one registration of a superblock under a
  device number, holding `s_passive`. One device can map to several
  superblocks and one superblock to several devices
  (`fs_bdev_file_open_by_dev()`); `user_get_super()` and the block holder
  callbacks walk it.
- `struct fs_struct` per task: `struct task_struct` has two pointers. `real_fs`
  is the one the task owns and `fs/proc/base.c` reports; `fs` is the one
  `scoped_with_init_fs()` swaps to `userspace_init_fs` for a scope.
- `init_fs`: its root and cwd are a private nullfs mount, so a kthread
  sharing it resolves nothing unless it uses `scoped_with_init_fs()`. PID 1
  gets its own copy, which `init_userspace_fs()` moves to the rootfs.
- failfs (`fs/failfs.c`): one internal mount in no namespace whose root fails
  every walk with `-EOPNOTSUPP`. A task makes it its root or cwd by passing
  `FD_FAILFS_ROOT`; see `fs/open.c`.
