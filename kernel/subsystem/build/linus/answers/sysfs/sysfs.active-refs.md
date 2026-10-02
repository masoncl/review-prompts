- `kernfs_fop_open()` in `fs/kernfs/file.c`: takes no counted reference on the
  node; `of->kn` is a plain pointer.
- Node pin for an open file: the `kernfs_get()` in `kernfs_init_inode()`
  (`fs/kernfs/inode.c`), held by the inode until `kernfs_evict_inode()`.
- `kernfs_get_active_of()`: what the file operations call; it fails on
  `of->released` before it tries `kernfs_get_active()` (see Open files at
  removal). Of the file operations in `fs/kernfs/file.c`, only
  `kernfs_fop_open()` calls `kernfs_get_active()` directly.
- `kobject_cleanup()` in `lib/kobject.c`: calls `__kobject_del()` when
  `state_in_sysfs` is set, before `t->release(kobj)`, so the ktype release
  runs after the drain even if the owner never called `kobject_del()`.
- Data other than the kobject: sysfs takes no reference on it;
  `sysfs_kf_seq_show()` and `sysfs_kf_write()` pass only the kobject and
  `of->kn->priv`. Sysfs orders its freeing against callbacks only through the
  drain: it can be freed once the removal of the file has returned, or from
  the ktype `release()`.
