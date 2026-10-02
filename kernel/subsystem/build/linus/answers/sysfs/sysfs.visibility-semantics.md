- `is_visible_const`: a second text callback in `struct attribute_group`,
  taking `const struct attribute *`; `create_files()` calls it when
  `is_visible` is NULL, with the same index and the same treatment of the
  result.
- `SYSFS_GROUP_INVISIBLE` in a callback result: `create_files()` clears it
  before the zero test, so a result of only that bit skips the file.
- Bits outside `SYSFS_PREALLOC | 0664`: `WARN()` "Invalid permissions", then
  dropped; the test also runs on the static mode when there is no callback.
- Evaluated again by the ownership walk as well as by `sysfs_update_group()`
  and `sysfs_update_groups()`: `sysfs_group_attrs_change_owner()` calls the
  callbacks to decide which names to look up, and does not apply the mode.
