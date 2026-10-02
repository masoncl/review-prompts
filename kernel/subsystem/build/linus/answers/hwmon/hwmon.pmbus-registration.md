- `pmbus_do_probe()` calls `devm_hwmon_device_register_with_groups()`, not
  `devm_hwmon_device_register_with_info()`.
- `drivers/hwmon/pmbus/` contains no `struct hwmon_chip_info`,
  `struct hwmon_channel_info` or `struct hwmon_ops`. A patch that adds
  `is_visible`/`read`/`write` ops to a PMBus chip driver has nothing to attach
  them to.
- Attribute type: `struct sensor_device_attribute` embedded in the private
  sensor, boolean, label and samples structs. `index` is -1 for all but
  booleans, where it packs page, register and status mask; see
  `pb_reg_to_index()`.
- Zero attributes found: `pmbus_do_probe()` returns `-ENODEV` and registers
  no hwmon device.
- Thermal zones: registered by the PMBus core itself, not by the hwmon core.
  `pmbus_add_sensor()` calls `pmbus_thermal_add_sensor()` for each
  `PSC_TEMPERATURE` sensor of type "input".
- Thermal ordering: the zone exists before the hwmon device does.
  `pmbus_thermal_get_temp()` reports 0 and touches no register while
  `data->hwmon_dev` is NULL.
- Callbacks in a chip driver's `info->groups`: `dev` is the hwmon device. The
  client is `to_i2c_client(dev->parent)`, as in `isl68137_avs_enable_show()`.
  The hwmon device's drvdata is the core's private `struct pmbus_data`.
- `pec` attribute: created with `device_create_file()` on the I2C client
  device in `pmbus_init_common()`, only when `I2C_CLIENT_PEC` ended up set. It
  is not part of the hwmon groups.
