- `kernfs_remove_by_name_ns()` with a NULL parent: `WARN()` "kernfs: can not
  remove '%s', no directory", returns `-ENOENT`.
- `kobj->sd` is NULL after `sysfs_remove_dir()`, so `sysfs_remove_file()`,
  `sysfs_remove_bin_file()` and `sysfs_remove_link()` on that kobject hit that
  `WARN()`.
- Child kobject whose ancestor's directory was removed: its `kobj->sd` is
  stale, not NULL (pinned by `sysfs_get()` in `create_dir()`), so removals by
  name under it return `-ENOENT` silently, with no `WARN()`.
