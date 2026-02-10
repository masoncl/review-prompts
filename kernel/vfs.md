# VFS Subsystem Details

## Inode Locking Hierarchy

Violating the inode locking order causes deadlocks between concurrent
directory operations (e.g., rename vs unlink on overlapping directories).
Using the wrong `i_rwsem` subclass defeats lockdep's ability to detect
ordering violations, hiding real deadlocks until production.

- Directory operations acquire the parent inode's `i_rwsem` with
  `inode_lock_nested(dir, I_MUTEX_PARENT)` before looking up or modifying
  children. The core helper `__start_dirop()` in `fs/namei.c` enforces this
  for mkdir, rmdir, unlink, mknod, symlink, and link creation.
- The lock ordering is parent before child: the parent directory lock
  (`I_MUTEX_PARENT`, subclass 1) must be acquired before the child inode lock
  (`I_MUTEX_NORMAL`, subclass 0). See the comment above
  `enum inode_i_mutex_lock_class` in `include/linux/fs.h`.
- Rename requires locks on both parent directories. `lock_rename()` in
  `fs/namei.c` acquires the filesystem-wide `s_vfs_rename_mutex` first (to
  prevent concurrent renames from creating directory loops), then locks both
  parents via `lock_two_directories()`. The ancestor directory gets
  `I_MUTEX_PARENT` (subclass 1) and the descendant gets `I_MUTEX_PARENT2`
  (subclass 5). Subdirectories that change parent in a rename are locked
  with `I_MUTEX_CHILD` (subclass 2). Non-directory children are locked
  with `I_MUTEX_NORMAL` / `I_MUTEX_NONDIR2` via
  `lock_two_nondirectories()`.

| Subclass | Constant | Purpose |
|----------|----------|---------|
| 0 | `I_MUTEX_NORMAL` | Object of the current VFS operation |
| 1 | `I_MUTEX_PARENT` | Parent directory |
| 2 | `I_MUTEX_CHILD` | Child/target (rename subdirectories) |
| 3 | `I_MUTEX_XATTR` | xattr operations |
| 4 | `I_MUTEX_NONDIR2` | Second non-directory (rename of two non-dirs) |
| 5 | `I_MUTEX_PARENT2` | Second parent (cross-directory rename) |

**`i_rwsem` scope:** `inode->i_rwsem` is a `struct rw_semaphore` that
protects more than just file data. It is held exclusive for directory
mutations (`create`, `link`, `unlink`, `rmdir`, `rename`, `mkdir`, `mknod`,
`symlink`), file attribute changes (`setattr`, `fileattr_set`), and the
buffered write path (`write_begin`/`write_end`, truncate). It is held shared
for directory `lookup` and `atomic_open` without `O_CREAT`. See the locking
table in `Documentation/filesystems/locking.rst`.

## Dentry States and Instantiation

Calling `d_instantiate()` on a dentry that is already associated with an
inode triggers a `BUG_ON`, crashing the kernel. Confusing negative and
positive dentries leads to NULL pointer dereferences when accessing
`d_inode` on a negative dentry, or corruption when re-instantiating an
already-positive dentry.

- A **negative dentry** records that a name does not exist. It has
  `DCACHE_MISS_TYPE` in its type flags and `d_inode == NULL`. The canonical
  check is `d_is_negative()` in `include/linux/dcache.h`, which checks the
  type flags. `d_really_is_negative()` checks the raw `d_inode` pointer
  directly and should only be used by a filesystem examining its own
  dentries (the distinction matters for overlay/union filesystems).
- A **positive dentry** has a non-`DCACHE_MISS_TYPE` entry type and
  `d_inode != NULL`. Check with `d_is_positive()` or
  `d_really_is_positive()`.
- `d_instantiate()` in `fs/dcache.c` turns a negative dentry into a
  positive one. Preconditions:
  1. The dentry must not already be on any inode's alias list — enforced by
     `BUG_ON(!hlist_unhashed(&entry->d_u.d_alias))` in `d_instantiate()`.
  2. The dentry must not be in the middle of a parallel lookup — enforced by
     `WARN_ON(d_in_lookup(dentry))` in `__d_instantiate()`.
  3. The caller must have already incremented the inode's reference count.
- `d_instantiate()` does NOT hash the dentry. Use `d_add()` (which combines
  instantiation and hashing via `__d_rehash()`) when the dentry also needs
  to be hashed.
- `d_instantiate_new()` is for inodes obtained via `iget_locked()` or
  `iget5_locked()`, which set the `I_NEW` flag. It combines
  `d_instantiate()` with `unlock_new_inode()`, clearing `I_NEW | I_CREATING`
  and waking waiters. It requires a non-NULL inode (`BUG_ON(!inode)`).
  Do not use it with `new_inode()`, which does not set `I_NEW`.

## Path Walking Modes

Incorrect transitions between RCU-walk and REF-walk cause use-after-free
on dentries or mount structures (if references are not taken before
dropping RCU protection), or stale path resolution if seqcount validation
is skipped (the walk may follow a dentry that was concurrently renamed or
moved).

- **RCU-walk** (`LOOKUP_RCU`): Lockless path traversal that avoids all
  locks and reference counts. Uses `rcu_read_lock()` for the entire walk
  and samples sequence numbers from `mount_lock` (a seqlock) and per-dentry
  `d_seq` (a `seqcount_spinlock_t`) to detect concurrent modifications. On
  any inconsistency, it returns `-ECHILD`. See `path_init()` and
  `lookup_fast()` in `fs/namei.c`.
- **REF-walk**: Takes `d_lockref` references on dentries and per-CPU
  `mnt_count` references on vfsmounts. On dcache miss, `lookup_slow()`
  takes `i_rwsem` shared on the directory to perform a filesystem lookup.
  REF-walk does not fail due to concurrency (never returns `-ECHILD`), but
  can fail with standard filesystem errors (`-ENOENT`, `-ENOTDIR`, `-EPERM`,
  `-ELOOP`, `-ESTALE`).
- The kernel always attempts RCU-walk first, falling back to REF-walk on
  failure. The pattern in `filename_lookup()` in `fs/namei.c` is:
  1. Try `path_lookupat()` with `LOOKUP_RCU`.
  2. On `-ECHILD`, retry without `LOOKUP_RCU` (REF-walk).
  3. On `-ESTALE`, retry with `LOOKUP_REVAL` (force revalidation).
- Mid-walk transition from RCU-walk to REF-walk is attempted via
  `try_to_unlazy()` in `fs/namei.c`, which takes references on the current
  path and validates `d_seq`. If validation fails (seqcount changed), it
  returns `false` and the caller returns `-ECHILD` for a full restart. The
  transition is one-way: once in REF-walk, the kernel never switches back
  to RCU-walk.

## Permission Checks

Missing or misordered permission checks allow unauthorized file access —
a security bypass. Checking permissions after the file is already opened
or modified is too late.

- `may_open()` in `fs/namei.c` is the gate for file open operations. It
  checks file type restrictions (e.g., no writing to directories, no exec
  on non-regular files), device access (`may_open_dev()`), and delegates to
  `inode_permission()` for POSIX permission checks. It is `static` to
  `namei.c`.
- `inode_permission()` in `fs/namei.c` is the exported, central permission
  check function. It chains through: superblock-level checks (read-only
  filesystem), immutable file checks, unmapped ID checks,
  `do_inode_permission()` (POSIX/filesystem-specific), `devcgroup_inode_permission()`
  (cgroup device controller), and `security_inode_permission()` (LSM hooks).
- `file_permission()` in `include/linux/fs.h` is a convenience wrapper that
  extracts the idmap and inode from a `struct file` and calls
  `inode_permission()`.

## File Operations

Using a stale or improperly referenced `f_op` pointer causes
use-after-free if the backing module is unloaded, or NULL dereferences if
the operations struct is missing.

- `file->f_op` is initialized to `NULL` in `init_file()` in
  `fs/file_table.c` but is always set to a valid pointer before the file is
  usable. For `O_PATH` files, it is set to `&empty_fops` (a static
  all-NULL-members struct), not `NULL`. For all other files,
  `do_dentry_open()` in `fs/open.c` sets it via `fops_get(inode->i_fop)`;
  if that returns `NULL`, the open fails with `-ENODEV` and a `WARN_ON`.
- Reassignment of `f_op` after file creation requires `replace_fops()`,
  which calls `fops_put()` on the old operations and properly stores the
  new pointer. `fops_get()`/`fops_put()` manage the backing module's
  reference count. Raw pointer assignment bypasses module refcounting and
  risks use-after-free on module unload. The canonical example is
  `chrdev_open()` in `fs/char_dev.c`, which replaces `def_chr_fops` with
  the device-specific operations.
- `file->private_data` is initialized to `NULL` in `init_file()` and lives
  for the entire lifetime of the `struct file`. The kernel does NOT
  automatically free what it points to — the `.release()` file operation
  callback is responsible for cleanup.

## Quick Checks

- **`sb->s_umount` for superblock operations**: `sb->s_umount` is a
  `struct rw_semaphore` protecting superblock lifecycle operations. It is
  held exclusive for `put_super`, `freeze_fs`, `unfreeze_fs`, and
  `remount_fs`; held shared for `sync_fs`. See
  `Documentation/filesystems/locking.rst`.
- **`dget`/`dput` for dentry references**: `dget()` increments the dentry
  reference count via `lockref_get()`. `dput()` decrements it and may free
  the dentry when the count reaches zero. Calling `dget()` on a
  zero-refcount dentry is a bug.
- **Lock drop and reacquire**: When `i_rwsem` or another VFS lock is
  dropped and retaken (e.g., to avoid lock ordering violations or to
  sleep), verify the code re-validates all protected state after
  reacquiring — the dentry may have gone negative, the inode may have been
  evicted, or the directory may have been removed.
