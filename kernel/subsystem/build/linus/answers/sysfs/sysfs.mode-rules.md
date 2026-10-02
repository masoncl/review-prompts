- `VERIFY_OCTAL_PERMISSIONS()` is defined in `include/linux/sysfs.h`.
- `VERIFY_OCTAL_PERMISSIONS()` accepts execute bits and group write; 0775
  passes. It rejects only values outside 0..0777, other-write, and a read or
  write bit that is weaker for user than for group (or group than other, for
  read).
- `__BIN_ATTR()` does not use `VERIFY_OCTAL_PERMISSIONS()`; nor does
  `__ATTR_IGNORE_LOCKDEP()` under `CONFIG_DEBUG_LOCK_ALLOC`.
- The WARN "Invalid permissions" and the mask to `SYSFS_PREALLOC | 0664` are
  in `create_files()` in `fs/sysfs/group.c`, not in
  `sysfs_add_file_mode_ns()`.
- `sysfs_add_file_mode_ns()` and `sysfs_add_bin_file_mode_ns()`: only
  `mode & 0777`, no WARN on the mode.
- `sysfs_create_file_ns()`, `sysfs_create_bin_file()`,
  `sysfs_add_file_to_group()` and `sysfs_merge_group()` pass `attr->mode`
  without the 0664 mask, so execute or other-write bits set at run time
  survive there.
- Mode without a matching callback: `device_create_file()` WARNs, and it
  tests both members of each pair; no creation function in `fs/sysfs/`
  checks.
- `kernfs_fop_open()` refusal for a missing mode bit or a missing kernfs op:
  `-EACCES`, not `-EINVAL`; the test runs only under
  `KERNFS_ROOT_EXTRA_OPEN_PERM_CHECK`, which `sysfs_init()` sets.
- A 0644 device attribute with no `store` and no `store_const`: opens for
  write, because the callback half of the open check looks at the kernfs
  table, not at the attribute; the write returns `-EIO` from
  `dev_attr_store()`.
