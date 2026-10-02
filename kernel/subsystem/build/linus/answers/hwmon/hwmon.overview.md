- `struct hwmon_ops` callbacks: only `is_visible` receives `drvdata`; `read`,
  `read_string` and `write` receive the hwmon class `struct device *`, and
  reach the driver data with `dev_get_drvdata()`.
- `hwmon_energy64`: the `long *val` given to `read` points at an `s64`, and the
  driver casts it back; see `ina238_read()` in `drivers/hwmon/ina238.c` for
  the cast.
- `struct hwmon_thermal_data`: exists only for a channel that
  `devm_thermal_of_zone_register()` attached to a zone; on `-ENODEV` the
  channel is skipped and registration still succeeds, see
  `hwmon_thermal_add_sensor()`.
- `hwmon_device_register_for_thermal()`: the bridge in the other direction,
  exported in namespace `HWMON_THERMAL` and called only from
  `drivers/thermal/thermal_hwmon.c`. The hwmon device has no
  `struct hwmon_chip_info` and no groups, its parent is a thermal zone's
  `struct device`, and the files are added later with `device_create_file()`.
- `struct thermal_hwmon_device` in `drivers/thermal/thermal_hwmon.c`: one
  hwmon device shared by every thermal zone of the same type; its parent is
  the zone that created it. `thermal_remove_hwmon_sysfs()` for the parent
  zone unregisters the hwmon device and removes the files of every zone; for
  another zone it removes only that zone's files.
- `struct hwmon_chip_info` and `name`: the core stores both pointers without
  copying, and each `struct hwmon_device_attribute` stores the ops pointer.
  The table need not be static; `lm90_probe()` in `drivers/hwmon/lm90.c`
  builds it inside its driver data.
