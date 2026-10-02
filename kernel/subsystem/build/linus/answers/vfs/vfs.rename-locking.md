- `lock_rename()`, `lock_rename_child()`, `unlock_rename()` and
  `lock_two_directories()`: all `static` in `fs/namei.c`, declared in no
  header, not exported.
- `vfs_rename()`: exported; it expects the parents locked already.
- `lock_rename()`: when `p1 != p2`, takes `s_vfs_rename_mutex` of `p1->d_sb`
  with no test that the two directories share a superblock.
- `-EXDEV` from `lock_two_directories()`: returned when the `d_parent` walks
  find no common ancestor; that branch drops `s_vfs_rename_mutex` itself.
- Directory locked second by `lock_two_directories()`: always
  `I_MUTEX_PARENT2`; it is `p1` when `p2` is an ancestor of `p1`.
- `lock_rename_child()`: no retry loop. It tries once without the mutex,
  then decides under `s_vfs_rename_mutex`.
- `lock_rename_child()` returning NULL: can mean one directory locked and
  the mutex not held; `unlock_rename()` handles that because it is then
  called with `p1 == p2`.
