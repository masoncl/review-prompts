- `visible` and `is_visible` both set: `hwmon_is_visible()` returns
  `ops->visible` and never calls `ops->is_visible()`; the callback runs only
  when `visible` is 0.
- First round of calls: from `hwmon_genattr()` under `__hwmon_create_attrs()`,
  before `device_register()`; the callback gets the `drvdata` passed to
  registration and the hwmon device is not registered yet.
- Second call: `hwmon_thermal_register_sensors()` asks again for
  `hwmon_temp_input` of each `hwmon_temp` channel that has `HWMON_T_INPUT`,
  after `device_register()`; any non-zero answer leads to
  `hwmon_thermal_add_sensor()`.
- Neither `visible` nor `is_visible` set: rejected with `-EINVAL` in
  `hwmon_device_register_with_info()`, not in `__hwmon_device_register()`.
