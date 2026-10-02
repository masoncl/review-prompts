- Only `HWMON_C_REGISTER_TZ` and `HWMON_C_PEC` produce no file on the hwmon
  device; every other enumerator of `enum hwmon_chip_attributes` has a string
  in `hwmon_chip_attrs`, `hwmon_chip_update_interval_us` included.
- `is_visible` is never asked about either bit; a driver that wants one off
  leaves it out of `config[0]` before registering, as `lm90_probe()` in
  `drivers/hwmon/lm90.c` does for `HWMON_C_PEC`.
- One condition in `__hwmon_device_register()` encloses both bits:
  `hdev->of_node` set, `chip->ops->read` set, and `chip->info[0]->type ==
  hwmon_chip`.
- `HWMON_C_PEC` without an `of_node` on the hwmon device, or without
  `ops->read`: ignored, no `pec` file, registration succeeds.
- `hdev->of_node`: the inherited node described under "Firmware node of the
  device"; `devm_thermal_of_zone_register()` looks up zones by that node.
- Thermal sensor id: the 0-based channel index, not the number in
  `temp%d_input`.
- `-ENODEV` from `devm_thermal_of_zone_register()`: `dev_info()` and the scan
  continues; any other error fails the registration.
- There is no hwmon_pec_attr_group; `hwmon_pec_register()` creates the one
  file `dev_attr_pec` on the I2C client with `device_create_file()`, and only
  when the adapter has `I2C_FUNC_SMBUS_PEC`; otherwise it returns 0 and
  creates nothing.
- `HWMON_C_PEC`, once the condition in `__hwmon_device_register()` holds, with
  a parent that `i2c_verify_client()` rejects: `hwmon_pec_register()` returns
  `-EINVAL` and the registration fails.
- `HWMON_C_PEC` when `IS_REACHABLE(CONFIG_I2C)` is false: the stub
  `hwmon_pec_register()` returns `-EINVAL`, with the same result.
- `pec_store()`: finds the hwmon device with `device_find_child()` and
  `is_hwmon_device()`, so it acts on the first hwmon child of the I2C client.
- `pec_store()` with no `ops->write`: skips the driver call and still changes
  `I2C_CLIENT_PEC` in `client->flags`.
