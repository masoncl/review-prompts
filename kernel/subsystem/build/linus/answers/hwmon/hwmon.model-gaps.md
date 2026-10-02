- Models take the comment above `hwmon_match_device()` in
  `drivers/hwmon/hwmon.c` at its word; it still describes a single mutex
  for PEC. `pec_store()` takes `hwdev->lock` of the hwmon child, and the
  file defines no global mutex.
- Models expect non-const sysfs handler arguments in the core.
  `hwmon_attr_show()`, `hwmon_attr_show_string()`, `hwmon_attr_store()` and
  `pec_store()` take `const struct device_attribute *`, and
  `hwmon_dev_attr_group` sets `is_visible_const`; see
  `include/linux/device.h` and `include/linux/sysfs.h`.
- Models do not know `HWMON_C_UPDATE_INTERVAL_US`. It is in
  `include/linux/hwmon.h` and creates `update_interval_us`.
- Models take every `hwmon_lock` to be the core helper. Several drivers have
  a private mutex member of that name, for example in
  `drivers/hwmon/da9052-hwmon.c` and `drivers/hwmon/occ/common.h`.
- Models take PMBus to get events from the hwmon core. It notifies through
  `pmbus_notify()`, which calls `sysfs_notify()` and `kobject_uevent()`; it
  does not call `hwmon_notify_event()`.
