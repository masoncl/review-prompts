- `drivers/mfd/mfd-core.c`: has no hotplug handling; the wrapper differs from
  `mfd_add_devices()` only in its arguments.
- Callers of `mfd_add_hotplug_devices()`: include parents on the platform
  bus that want automatic ids, for example `ec_device_probe()` in
  `drivers/mfd/cros_ec_dev.c`.
- `cell->id` with `PLATFORM_DEVID_AUTO`: ignored by `mfd_add_device()`;
  `pdev->id` is the allocated id, `mfd_get_cell(pdev)->id` is the cell's.
- `_dln2_transfer()` after `dln2_stop()`, while `disconnect` is set: returns
  `-ENODEV`. `-ESHUTDOWN` appears in `drivers/mfd/dln2.c` only as a URB
  status in the RX completion.
- `dln2_free()`: frees only the RX URBs. `struct dln2_dev` comes from
  `devm_kzalloc()` on the interface device, so it outlives
  `dln2_disconnect()`.
- Child `remove()` callbacks in `dln2_disconnect()`: run inside
  `mfd_remove_devices()`, after `dln2_stop()`, and call back into the parent.
  `dln2_i2c_remove()` and `dln2_spi_remove()` call `dln2_transfer()` and get
  `-ENODEV`; `dln2_gpio_remove()` calls `dln2_unregister_event_cb()`.
