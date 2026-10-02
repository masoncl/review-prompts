| Job | Lock | Scope | Easy to miss |
|---|---|---|---|
| tree of nodes | `kernfs_rwsem` | per root | field of `struct kernfs_root` in `fs/kernfs/kernfs-internal.h` |
| inode attributes | `kernfs_iattr_rwsem` | per root | also covers `dir.subdirs`, `dir.rev` and the `KERNFS_REMOVING` marking pass; xattr sets use the hashed mutex instead |
| list of superblocks | `kernfs_supers_rwsem` | per root | written in `kernfs_get_tree()` and `kernfs_kill_sb()`; the struct comment naming `kernfs_rwsem` does not match the code |
| renames | `kernfs_rename_lock`, an `rwlock_t` | per root | write-locked in `kernfs_rename_ns()` only when the parent changes; a same-parent rename swaps `name` under RCU |
| per-node list of open files | `node_mutex[]` in `struct kernfs_global_locks` | hashed per node, one global array | via `kernfs_node_lock_ptr()`; `kernfs_open_file_mutex_ptr()` and `kernfs_open_file_mutex_lock()` are wrappers in `fs/kernfs/file.c` |
| a single open file | `mutex` in `struct kernfs_open_file` | per open file | nests outside the active reference |
| notification list | `kernfs_notify_lock` | global | static spinlock in `fs/kernfs/file.c` |
| id allocator | `kernfs_idr_lock`, a spinlock | per root | lookup by id uses RCU only |

- Names absent from this tree: open_file_mutex[], kernfs_open_node_lock.
- Order in removal:
  1. `kernfs_remove()`: `kernfs_supers_rwsem` for read, then `kernfs_rwsem` for
     write; `__kernfs_remove()` asserts both.
  2. Marking pass: `kernfs_iattr_rwsem` for write, nested inside.
  3. `kernfs_drain()`: releases `kernfs_rwsem`, then `kernfs_supers_rwsem`.
  4. `kernfs_drain_open_files()`: hashed node mutex, taken alone.
  5. `kernfs_drain()` exit: `kernfs_supers_rwsem` for read, then `kernfs_rwsem`
     for write.
  6. `kernfs_unlink_sibling()` and the cleanup after it: `kernfs_iattr_rwsem`
     for write, nested inside.
  7. Last `kernfs_put()`: `kernfs_idr_lock`.
- `kernfs_remove_self()` and `kernfs_remove_by_name_ns()`: same first two locks
  in the same order.
- `kernfs_show()`: does not take `kernfs_supers_rwsem`; it takes `kernfs_rwsem`
  and calls `kernfs_drain()` with `drop_supers` false.
- Removal does not take `kernfs_rename_lock`, `kernfs_notify_lock` or the
  `mutex` of any `struct kernfs_open_file`.
