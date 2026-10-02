- Models take `device_change_owner()` to work for any device in sysfs. For a
  device without a class it returns `-EINVAL` from the `class_to_subsys()`
  test, after ownership of the directory and groups has already changed.
- `struct kobj_type` without `release()`: at the final put nothing in
  `kobject_cleanup()` frees the object.
- Models take a file operation to fail with `-ENODEV` only when the node is
  deactivated. `kernfs_get_active_of()` in `fs/kernfs/file.c` also fails once
  `of->released` is set; only `kernfs_release_file()` sets it, and its callers
  call it only for a node with `KERNFS_HAS_RELEASE`. No sysfs table has a
  `release` op, so it is never set on a sysfs file.
- Models name kernfs_create_file_ns() and kernfs_create_file() as the file
  constructors. Neither exists here; callers use `__kernfs_create_file()` and
  pass the lockdep key, or NULL, themselves.
