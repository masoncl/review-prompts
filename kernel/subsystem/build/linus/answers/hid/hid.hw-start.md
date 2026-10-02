- Stop from a devm action: `mcp2221_probe()` registers
  `mcp2221_hid_unregister()` with `devm_add_action_or_reset()`; for what such
  a driver needs in `remove` see "Stopping hardware from devres".
- After a failed `hid_hw_start()`: when `hid_connect()` failed,
  `ll_driver->stop()` has already run; when `ll_driver->start()` failed, it
  was not called. Either way the driver does not call `hid_hw_stop()`.
