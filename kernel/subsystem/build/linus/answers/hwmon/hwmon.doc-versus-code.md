- Invalid name: `Documentation/hwmon/hwmon-kernel-api.rst` says it "will be
  rejected"; `__hwmon_device_register()` only calls `dev_warn()` for an empty
  name or one that contains `-`, `*`, space, tab or newline, and registers the
  device.
- NULL name: the document says the name is then derived from the parent; only
  `devm_hwmon_device_register_with_info()` does that, through
  `devm_hwmon_sanitize_name()` on `dev_name()`.
- `hwmon_sanitize_name()` and `devm_hwmon_sanitize_name()`: return `ERR_PTR()`
  on failure, never NULL; the document does not say so.
- `is_visible`: the document calls it mandatory;
  `hwmon_device_register_with_info()` accepts ops with either `visible` or
  `is_visible` set.
- `struct hwmon_channel_info` listing: shows `u32 *config`; the header has
  `const u32 *config`.
- Sensor types table: lists `hwmon_energy64`, lacks `hwmon_intrusion`; the
  prefix table has no row for `HWMON_INTRUSION_ALARM` and
  `HWMON_INTRUSION_BEEP`.
- NULL `dev` or `chip`: the document states that both must not be NULL, and
  `hwmon_device_register_with_info()` returns `-EINVAL` for either.
- `HWMON_C_REGISTER_TZ` and `HWMON_C_PEC`: the document does not give the
  conditions. `__hwmon_device_register()` honours them only if
  `chip->info[0]` has type `hwmon_chip`, `chip->ops->read` is set, and the
  parent or one of its ancestors has an `of_node`.
- `HWMON_C_REGISTER_TZ` without `CONFIG_THERMAL_OF`:
  `hwmon_thermal_register_sensors()` returns 0 and registers nothing.
- Device-level `label`: the document does not mention it;
  `__hwmon_device_register()` creates it from the firmware property "label" of
  the parent, and fails the registration if the property is present but cannot
  be read as a string.
- `val` of the write callback: the document does not say how it is produced;
  `hwmon_attr_store()` parses with `kstrtol()` in base 10 and returns its error
  before the callback runs, so a string that is not a number never reaches the
  driver as 0.
