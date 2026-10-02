- Every registered client is created by `i2c_new_client_device()`; the rows
  below are the ones easy to miss.

| Way | Goes through | Who unregisters |
|---|---|---|
| SMBus alert, automatic | `i2c_setup_smbus_alert()` from `i2c_register_adapter()`, when the parent has interrupt name "smbus_alert" or property "smbalert-gpios" (`CONFIG_I2C_SMBUS`) | core, in `i2c_deregister_clients()` |
| Host-notify target | `i2c_new_slave_host_notify_device()` in `drivers/i2c/i2c-smbus.c` | caller, with `i2c_free_slave_host_notify_device()`, which also unregisters the slave callback and frees the platform data |
| Extra ACPI I2cSerialBus resource | `i2c_acpi_new_device_by_fwnode()` | caller, with `i2c_unregister_device()` |

- Detected clients: kept on `driver->clients`; sysfs clients: kept on
  `adap->userspace_clients`; both linked through `client->detected`. There are
  no I2C_CLIENT_AUTO or I2C_CLIENT_USER flags.
- `i2c_deregister_clients()`: unregisters every child client of the adapter,
  caller-owned ones included; clients named "dummy" go in the second pass.
- Static board info: scanned whenever `adap->nr` is below
  `__i2c_first_dynamic_bus_num`; that includes adapters numbered by a DT
  "i2c" alias through `i2c_add_adapter()`.
- `i2c_detect()` runs for each adapter and driver pair, from
  `__process_new_adapter()` and `__process_new_driver()`, and probes only when
  all hold:
  - the driver has both `detect` and `address_list`;
  - `adapter->class` is not exactly `I2C_CLASS_DEPRECATED`;
  - `adapter->class & driver->class` is non-zero.
- `I2C_CLASS_HWMON` is the only class bit defined besides
  `I2C_CLASS_DEPRECATED`.
- Mux channel adapters: `i2c_mux_add_adapter()` in `drivers/i2c/i2c-mux.c`
  never sets `class`, so they are not probed.
- `i2c_detect()` makes no functionality test of its own; the presence probe is
  `i2c_default_probe()`, run by the core in `i2c_detect_address()` before
  `driver->detect` is called. It picks its method with
  `i2c_check_functionality()` and reports nothing present when the adapter
  supports no suitable method.
