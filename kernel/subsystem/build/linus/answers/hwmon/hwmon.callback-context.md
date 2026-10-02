- Attributes passed in `extra_groups`: the core does not wrap them, so they
  run without the core lock (`lock` in `struct hwmon_device`) unless the
  driver takes `hwmon_lock()`.
- Lock order on the thermal paths: the `lock` of `struct thermal_zone_device`
  first, then the core lock.
- Thermal zones are registered only when all hold: `CONFIG_THERMAL_OF`,
  `chip->ops->read` set, `chip->info[0]->type == hwmon_chip` with
  `HWMON_C_REGISTER_TZ` in its first config word, an `of_node` on the
  parent or any ancestor, and per channel `HWMON_T_INPUT` set and visible;
  see `__hwmon_device_register()` and `hwmon_thermal_register_sensors()`.
- **Unsafe usage**: calling `hwmon_lock()` from inside `read`, `write` or
  `read_string`.
  - Unsafe: the core already holds the mutex, and `hwmon_lock()` is a plain
    `mutex_lock()`.
  - Safe: in code the core does not call, such as `shunt_resistor_store()` in
    `drivers/hwmon/ina2xx.c` or `lm90_update_alarms()` in
    `drivers/hwmon/lm90.c`.
