- `struct pmbus_platform_data` and the `PMBUS_SKIP_STATUS_CHECK`-style flags:
  defined in `include/linux/pmbus.h`, not in `drivers/hwmon/pmbus/pmbus.h`.
- `struct pmbus_sensor`, `struct pmbus_boolean`, `struct pmbus_label`,
  `struct pmbus_data`: private to `drivers/hwmon/pmbus/pmbus_core.c`; a chip
  driver cannot reach them.
- Regulator, debugfs, thermal and interrupt code: all inside `pmbus_core.c`;
  the regulator part is under `#if IS_ENABLED(CONFIG_REGULATOR)`. There is no
  separate regulator file.
- `pmbus_do_probe()`: stores the `struct pmbus_driver_info` pointer
  (`data->info = info`), it does not copy. The struct must live as long as the
  device.
- The info is written during `pmbus_do_probe()`: `identify` receives it
  non-const, and with `PMBUS_USE_COEFFICIENTS_CMD` `pmbus_init_coefficients()`
  fills `m[]`, `b[]`, `R[]`. A static info is shared by every device the
  driver binds.
- Second hand-over channel: the chip driver sets `dev->platform_data` to a
  `struct pmbus_platform_data` before `pmbus_do_probe()`; the core reads it
  with `dev_get_platdata()` into `data->flags`. See `pmbus_probe()` in
  `drivers/hwmon/pmbus/pmbus.c`.
- Client data: `pmbus_do_probe()` calls `i2c_set_clientdata()` with its own
  `struct pmbus_data`. A chip driver embeds the info in its private struct and
  recovers it with `pmbus_get_driver_info()` plus `container_of()`, as
  `to_isl68137_data()` does.
- `struct pmbus_driver_info` members that are easy to miss: the
  `write_byte_data` callback, the `ieee754` value of
  `enum pmbus_data_format`, and `have_pmbus_revision` with `pmbus_revision`
  for chips without `PMBUS_REVISION`.
- `pmbus_do_probe()` returns `-ENODEV` when `info` is NULL, when the adapter
  lacks byte/word SMBus functionality, or when `info->pages` is outside
  1..`PMBUS_PAGES` after `identify` ran. `pages` may be 0 on entry only if
  `identify` sets it.
- `Documentation/hwmon/pmbus-core.rst`: does not describe `pmbus_lock()`,
  `write_byte_data`, `groups` or the delay fields. Take the API from
  `drivers/hwmon/pmbus/pmbus.h`.
- There is no pmbus_do_remove here; what the core sets up is device-managed,
  except its debugfs files, which sit in `client->debugfs` and go when the
  I2C core removes that directory. A chip driver needs `remove` only for what
  it started itself.
