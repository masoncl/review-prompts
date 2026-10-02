- `CONFIG_THERMAL_OF`: tested with `IS_ENABLED()` at the top of
  `hwmon_thermal_register_sensors()` and of `hwmon_thermal_notify()`; there is
  one definition of each, no separate stub.
- No `IS_REACHABLE()` test guards the thermal code; `CONFIG_THERMAL` is `bool`
  in `drivers/thermal/Kconfig`.
- `chip->ops->read` NULL or `hdev->of_node` NULL: the test in
  `__hwmon_device_register()` fails, `HWMON_C_REGISTER_TZ` is ignored and
  registration succeeds with no zones.
