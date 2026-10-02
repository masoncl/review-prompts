- `read` during registration: for a sensor with a matching zone,
  `thermal_of_zone_register()` ends in `thermal_zone_device_enable()`, which
  calls `hwmon_thermal_get_temp()` synchronously.
- `write` during registration: the same update calls
  `thermal_zone_set_trips()`, which calls `hwmon_thermal_set_trips()` only when
  the read succeeded and a trip moved `low` or `high` off `-INT_MAX` /
  `INT_MAX`; it then writes `hwmon_temp_min` and `hwmon_temp_max`.
- `hwmon_thermal_set_trips()`: tests the `HWMON_T_MIN` and `HWMON_T_MAX` config
  bits, not `is_visible`; `write` can get an attribute that `is_visible` hid
  or made read-only, and `-EOPNOTSUPP` from it is ignored.
- lm75_probe is not in this tree; `lm75_generic_probe()` in
  `drivers/hwmon/lm75.c` shows chip setup, then registration, then
  `devm_request_threaded_irq()` with the hwmon device as cookie.
- **Potentially unsafe usage**: a callback that uses the hwmon device pointer
  the driver stores from the return value.
  - Unsafe: when the callback dereferences the stored pointer or passes it to
    `hwmon_notify_event()` with no NULL test; it is unset until registration
    returns.
  - Safe: use the `dev` argument of the callback, which the core passes as the
    hwmon device, as `lm75_read()` does with `dev_get_drvdata(dev)`.
  - Safe: test the stored pointer first, as `lm90_update_alarms_locked()` does
    with `data->hwmon_dev`.
