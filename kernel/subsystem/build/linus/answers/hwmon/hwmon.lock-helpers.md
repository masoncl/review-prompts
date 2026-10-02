- In-tree callers of `hwmon_lock()` or the guard: all register with info;
  none registers with groups.
- Guard: `DEFINE_GUARD(hwmon_lock, struct device *, ...)` in
  `include/linux/hwmon.h`, so `guard(hwmon_lock)(dev)` and
  `scoped_guard(hwmon_lock, dev)` both work; there is no try or interruptible
  variant.
- `hwmon_lock()` and `hwmon_unlock()`: do not check their argument. They have
  no NULL test and, unlike `hwmon_notify_event()`, no `is_hwmon_device()`
  test, so a parent device or an unset pointer is not caught;
  `to_hwmon_device()` is applied to it and, given the parent device, they
  lock unrelated memory.
- `extra_groups` show/store functions: the sysfs `dev` argument is already the
  hwmon device, so passing it straight to the guard is correct, as
  `heater_enable_store()` in `drivers/hwmon/sht4x.c` does.
- debugfs, cooling-device and interrupt code: the core passes it no hwmon
  device; it must use the pointer that registration returned, as
  `kb9002_fw_version_show()` in `drivers/hwmon/kb9002.c` does with
  `data->hwmon_dev`.
