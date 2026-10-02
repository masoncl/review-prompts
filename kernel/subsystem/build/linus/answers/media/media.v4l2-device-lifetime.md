- Holders other than the registered nodes: drivers call `v4l2_device_get()`
  directly for their own users, for example
  `drivers/media/usb/usbtv/usbtv-audio.c`.

| Function | Effect on the parent `struct device` |
|---|---|
| `v4l2_device_register()` | `get_device(dev)`; sets drvdata only if it is NULL |
| `v4l2_device_disconnect()` | clears drvdata if it points to `v4l2_dev`; `put_device()`; `v4l2_dev->dev = NULL`; returns at once if `dev` is already NULL |
| `v4l2_device_unregister()` | calls `v4l2_device_disconnect()`, so it drops the device reference if still held; then unregisters subdevs |

- `v4l2_device_register()` with empty `name`: reads `dev->driver->name`, so
  `dev` must be bound to a driver or `name` must be preset.
- `v4l2_device_unregister()`: returns at once when `name[0]` is 0, and sets
  `name[0]` to 0 at the end, so a second call does nothing.
- `v4l2_i2c_subdev_unregister()` and `v4l2_spi_subdev_unregister()`: called
  from `v4l2_device_unregister()`; both leave a client that has a firmware
  node registered.
- Hot-unplug order with `v4l2_dev->release` set: see `gspca_disconnect()`
  and `gspca_release()` in `drivers/media/usb/gspca/gspca.c`;
  `v4l2_device_unregister()` runs from the release callback, not from
  disconnect.
