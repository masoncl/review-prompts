- `kernfs_remove_self()`: takes `kernfs_supers_rwsem` (read) and `kernfs_rwsem`
  (write) first, then drops the active reference; it restores the reference
  before unlocking.
- `sysfs_remove_file_self()` and `sysfs_break_active_protection()`: look the
  file up by `attr->name` directly under `kobj->sd`; an attribute inside a
  named group is not found.
- `sysfs_remove_file_self()`, file not found: `WARN_ON_ONCE()`, returns false.
- `sysfs_break_active_protection()`, file not found: returns NULL, has already
  dropped its kobject reference, and the active reference is still held.
- `sysfs_unbreak_active_protection()`: dereferences its argument, so it must
  not be given NULL; `sdev_store_delete()` in `drivers/scsi/scsi_sysfs.c`
  tests for NULL first.
- After `sysfs_break_active_protection()`: the callback removes its own file
  with plain `device_remove_file()`, not the self form; see
  `sdev_store_delete()`.
- `sysfs_break_active_protection()` with two writers: no arbitration, both
  run the removal. In `sdev_store_delete()` that is tolerated:
  `device_remove_file()` ignores a missing file while the directory exists,
  and `__scsi_remove_device()` returns early at `SDEV_DEL` under `scan_mutex`.
  `scsi_device_get()` there pins the device; it does not arbitrate.
- **Potentially unsafe usage**: touching the device or kobject after the
  callback's active reference was dropped.
  - Unsafe: when no reference on it was taken before the drop;
    `sysfs_remove_file_self()` and `device_remove_file_self()` take none.
    Once the node is unlinked no remover waits for this callback in
    `kernfs_drain()`, so the object can be freed under it. This covers a
    false return from `sysfs_remove_file_self()` too: by then the winner's
    whole operation has finished.
  - Safe: the callback takes the reference while the active reference is
    still held, as `sdev_store_delete()` does with `scsi_device_get()` before
    `sysfs_break_active_protection()`.
  - Safe: the kobject, between a non-NULL return of
    `sysfs_break_active_protection()` and `sysfs_unbreak_active_protection()`;
    the first does `kobject_get()` before it drops the active reference and
    the second puts it, as `interface_authorized_store()` in
    `drivers/usb/core/sysfs.c` relies on.
