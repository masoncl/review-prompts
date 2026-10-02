- `I_MUTEX_PARENT2`: spelled so; used only by `lock_two_directories()` in
  `fs/namei.c`, for the second directory, after `I_MUTEX_PARENT`.
- `I_MUTEX_CHILD`: not used for a parent in `lock_rename()`.
- `I_MUTEX_XATTR`: used by ext4 on EA inodes, in `fs/ext4/xattr.c`.
- lock_two_inodes(): not in this tree; `lock_two_nondirectories()` in
  `fs/inode.c` is the helper for two non-directories.
- `lookup_slow()` and `lookup_open()`: lock the parent with subclass 0
  (`inode_lock_shared()`, `inode_lock()`), not `I_MUTEX_PARENT`.
- Subclasses of the children in `vfs_rename()`:

| Source | Target | Source lock | Target lock |
|---|---|---|---|
| directory | any | `I_MUTEX_CHILD`, first | `inode_lock()`, second |
| non-directory | directory | `inode_lock()`, second | `I_MUTEX_CHILD`, first |
| non-directory | non-directory or none | `lock_two_nondirectories()` | same call |

- `__simple_recursive_removal()` in `fs/libfs.c`: locks each inode with
  `I_MUTEX_CHILD`, so a caller of `locked_recursive_removal()` holds the
  parent with `I_MUTEX_PARENT`, as `psinfo_lock_root()` does.
- Enum values are not a lock order: lockdep never compares two of them. See
  `look_up_lock_class()` in `kernel/locking/lockdep.c`; each key and subclass
  pair is one class, and the order is learned from use.
- Order the VFS uses: `I_MUTEX_PARENT`, `I_MUTEX_PARENT2`, `I_MUTEX_CHILD`,
  `I_MUTEX_NORMAL`, `I_MUTEX_NONDIR2`; that is 1, 5, 2, 0, 4.
- Subclass limit: below `MAX_LOCKDEP_SUBCLASSES`, which is 8; at or above it
  `__lock_acquire()` warns and turns lockdep off.
- Same key and same subclass held twice: `check_deadlock()` reports recursion
  whatever the real order; address order does not silence it, which is why
  `lock_two_nondirectories()` uses `I_MUTEX_NONDIR2` for the second inode.
- Lock keys: `inode_init_always_gfp()` gives every inode `i_mutex_key`. A
  directory moves to `i_mutex_dir_key` in
  `lockdep_annotate_inode_mutex_key()`, which is an empty stub without
  `CONFIG_DEBUG_LOCK_ALLOC`, or where the filesystem sets the class itself,
  as `xfs_setup_inode()` does.
- `lockdep_annotate_inode_mutex_key()`: called from `unlock_new_inode()`,
  `discard_new_inode()` and `d_instantiate_new()`, among others. A directory
  that never passes through it, in a filesystem that sets no class itself,
  shares a key with non-directories, so there only the subclass tells parent
  from child.
- **Potentially unsafe usage**: taking a second `i_rwsem` with the subclass
  already held.
  - Unsafe: when both inodes have the same lock key; `check_deadlock()`
    reports "possible recursive locking".
  - Safe: when the keys differ, as in `ecryptfs_do_unlink()` under
    `->unlink`: the eCryptfs directory and the lower directory are both held
    with `I_MUTEX_PARENT`, and `ecryptfs_get_tree()` refuses a lower
    filesystem of type eCryptfs, so the keys belong to two
    `struct file_system_type`.
  - Safe: when the second uses another subclass, as in `filename_rmdir()`:
    parent `I_MUTEX_PARENT` in `__start_dirop()`, child `inode_lock()` in
    `vfs_rmdir()`.
