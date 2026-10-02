- Models do not know that `i2c_new_client_device()` takes its own reference
  on `info->fwnode` with `fwnode_handle_get()`. `i2c_unregister_device()`
  drops it, except for a software node, which `device_remove_software_node()`
  releases.
- Models do not know `client->debugfs`: the core removes the directory
  recursively in `i2c_device_remove()` and on a failed probe, so a driver
  need not remove what it created there.
- Models do not know that `i2c_device_shutdown()` calls `disable_irq()` on
  `client->irq` when the bound driver has no `shutdown` callback and
  `client->irq` is above 0.
- Models take `i2c_register_spd_write_disable()` to instantiate every SPD
  type. It does not instantiate `spd5118` devices; see `i2c_register_spd()`
  in `drivers/i2c/i2c-smbus.c`.
- Models do not know that `struct i2c_board_info` has no `of_node` member: a
  device tree node is passed in `fwnode`, as `of_i2c_get_board_info()` does
  with `of_fwnode_handle()`.
- Models do not know that `drivers/i2c/i2c-atr.c` exports into the `"I2C_ATR"`
  namespace and `drivers/i2c/i2c-core-of-prober.c` into `"I2C_OF_PROBER"`: a
  module that calls them needs the matching `MODULE_IMPORT_NS()`.
- Models do not know `kzalloc_obj()`, `kzalloc_flex()` and `kmalloc_objs()`,
  which code in `drivers/i2c/` uses to allocate; they are defined in
  `include/linux/slab.h`.
- Models do not know `trace_call__i2c_slave()`, which `i2c_slave_event()`
  calls after testing `trace_i2c_slave_enabled()`; `include/linux/tracepoint.h`
  generates it for each tracepoint.
