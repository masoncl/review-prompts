- Earliest point for a create call: after `kobject_add()` or `device_add()`
  made the directory; before that `kobj->sd` is NULL and
  `sysfs_create_file_ns()` and `internal_create_group()` hit `WARN_ON()` and
  return `-EINVAL`.
- **Potentially unsafe usage**: `device_create_file()` or
  `sysfs_create_group()` on a device after `device_add()` returned.
  - Unsafe: when user space is to find the file on the "add" event and uevents
    were not suppressed; `device_add()` has already sent `KOBJ_ADD`.
  - Safe: `dev_set_uevent_suppress()` set before `device_add()`, cleared after
    the create calls, then `KOBJ_ADD` sent by hand, as
    `workqueue_sysfs_register()` does; `kobject_uevent_env()` drops events
    while `uevent_suppress` is set.
  - Safe: from a `BUS_NOTIFY_ADD_DEVICE` notifier, which `device_add()` calls
    before `kobject_uevent()`, as `usb_bus_notify()` does; removal is then
    explicit, on `BUS_NOTIFY_DEL_DEVICE`.
  - Safe: inside probe, as `max197_probe()` in `drivers/hwmon/max197.c`, for
    a file user space looks for on the "bind" event; `driver_bound()` sends
    `KOBJ_BIND` after `call_driver_probe()` returned. The driver removes the
    file itself.
- Plain kobject: `kobject_add()`, `kobject_init_and_add()` and
  `kobject_create_and_add()` send no uevent, so a create call after them
  races with nothing unless the caller sends `KOBJ_ADD` first;
  `driver_register()` sends it after the groups.
- `kset_register()` and `kset_create_and_add()`: call `kobject_uevent()` for
  `KOBJ_ADD` themselves, so files added to a kset directory always come after
  it.
- `devm_device_add_group()`: is itself a create call, and the only devm
  attribute helper declared in `include/linux/device.h`; there is no
  devm_device_add_groups.
- `devm_device_add_group()` removal: `devm_attr_group_remove()` runs from
  `devres_release_all()` in `device_unbind_cleanup()`, after the remove
  callback returned; driver `dev_groups` are removed before the callback is
  called.
- `faux_device_create_with_groups()`: no create call and no removal call, but
  `faux_probe()` creates the groups, so they appear after `KOBJ_ADD`.
