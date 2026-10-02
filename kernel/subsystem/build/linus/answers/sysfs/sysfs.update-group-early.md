- `kobj->sd` NULL with `update` set: `internal_create_group()` returns
  `-EINVAL` with no warning, for a named and an unnamed group alike.
- NULL `kobj`: `WARN_ON()` and `-EINVAL` in update mode too.
- After removal: `sysfs_remove_dir()` in `fs/sysfs/dir.c` sets `kobj->sd` to
  NULL, so an update after it gets the same silent `-EINVAL`.
- Nothing is recorded for later; the group appears only if a later call
  creates it, and that call evaluates the callbacks with the state at that
  time.
