- `thermal_zone_set_trips()` in `drivers/thermal/thermal_trip.c`: only logs the
  error that `hwmon_thermal_set_trips()` returns.
- `pec_store()`: defined in `drivers/hwmon/hwmon.c`. It calls `write` first and
  changes `I2C_CLIENT_PEC` only after 0 or `-EOPNOTSUPP`; any other error is
  returned with the flag unchanged.
- `pec_store()` input: parsed with `kstrtobool()`; returns `-ENODEV` when the
  client has no hwmon child device.
- `-EAGAIN` from `read` of `hwmon_temp_input` on the thermal path:
  `thermal_zone_recheck()` in `drivers/thermal/thermal_core.c` retries without
  its `dev_info()` message and without lengthening the delay. Any other error
  lengthens the delay and can end in `thermal_zone_broken_disable()`.
- `-ENODATA`: `Documentation/hwmon/sysfs-interface.rst` specifies it for a read
  of a sensor disabled through its `_enable` attribute; `ltc4282_read()` does
  this.
- Default branch: `-EOPNOTSUPP` is the predominant code under `drivers/hwmon`,
  but no file under `Documentation/hwmon` states it, and some in-tree default
  branches return `-EINVAL` or `-ENOTSUPP`.
- **Potentially unsafe usage**: a `write` that returns a code other than
  `-EOPNOTSUPP` for an attribute it does not implement.
  - Unsafe: when the core writes the attribute on its own: `hwmon_chip_pec`
    with `HWMON_C_PEC` set, or `hwmon_temp_min` / `hwmon_temp_max` with
    `HWMON_T_MIN` / `HWMON_T_MAX` set on a channel that has a thermal zone.
    `pec_store()` then fails and `hwmon_thermal_set_trips()` returns the error.
  - Safe: `lm90_chip_write()` in `drivers/hwmon/lm90.c` sets `HWMON_C_PEC`,
    does not handle `hwmon_chip_pec` and returns `-EOPNOTSUPP` from its default
    branch, which `pec_store()` ignores.
  - Safe: when the core writes nothing the driver lacks. `lm75_write()` in
    `drivers/hwmon/lm75.c` returns `-EINVAL` from its default branches, but
    `lm75_info` sets neither `HWMON_C_PEC` nor `HWMON_T_MIN`, and
    `lm75_write_temp()` handles `hwmon_temp_max`.
