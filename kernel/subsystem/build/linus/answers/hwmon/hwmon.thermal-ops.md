- `hwmon_thermal_ops`: sets `.get_temp` and `.set_trips` only.
- Locking: `hwmon_thermal_get_temp()` and `hwmon_thermal_set_trips()` hold
  `hwdev->lock` across the driver callback, the same mutex the sysfs paths
  take.
- `hwmon_thermal_set_trips()` lock order: the two early `return 0` cases (no
  `write`, no `hwmon_temp` entry) come before the lock is taken.
- `hwmon_thermal_set_trips()` gate: `HWMON_T_MIN` and `HWMON_T_MAX` in
  `config[tdata->index]` of the first `hwmon_temp` entry; it does not call
  `hwmon_is_visible()`.
- `low` and `high`: passed to `write` unchanged, including the `-INT_MAX` and
  `INT_MAX` that `__thermal_zone_device_update()` starts from; the core does
  not clamp them.
- `write` error in `hwmon_thermal_set_trips()`: `-EOPNOTSUPP` is ignored; any
  other non-zero value is returned at once, so a failed `hwmon_temp_min` write
  skips the `hwmon_temp_max` write.
