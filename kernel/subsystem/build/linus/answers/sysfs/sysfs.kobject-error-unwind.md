- Failed `sysfs_create_group()`, unnamed group: `remove_files()` removes every
  attribute name of the group from the directory, including a same-named file
  that was there before the call.
- `sysfs_remove_group()` on a group that is not there: no warning; a named
  group gets `pr_debug()` and return, an unnamed one a silent `-ENOENT` from
  `kernfs_remove_by_name_ns()`.
- **Unsafe usage**: `sysfs_remove_group()` or `sysfs_remove_file()` on a
  kobject whose directory is gone, so `kobj->sd` is NULL: after
  `kobject_del()` or after a failed add. A named group dereferences NULL in
  `kernfs_root()`; an unnamed group or a file hits `WARN()` for each name in
  `kernfs_remove_by_name_ns()`.
  - Safe: remove the group before `kobject_del()`, as `device_del()` does with
    `device_remove_attrs()`.
  - Safe: no removal at all when the next step is the delete or the final put,
    as `example_exit()` in `samples/kobject/kobject-example.c`;
    `sysfs_remove_dir()` removes the subtree.
- Order of puts between a parent and its child: not what keeps the parent
  alive; the child holds a reference on the parent from
  `kobject_add_internal()` until its own `kobject_del()` or the end of its
  `kobject_cleanup()`.
- Child directory after an ancestor's directory was removed: `create_dir()`
  took an extra reference with `sysfs_get()`, so the child's `kobj->sd` stays
  valid until its own `__kobject_del()`.
