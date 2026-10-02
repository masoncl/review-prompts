- There is no hid_stop() here; `hid_hw_stop()` in `drivers/hid/hid-core.c` is
  what calls `->stop()`.
- `usbhid_stop()`: runs inside `hid_destroy_device()` through `->stop()`, not
  before it; before that call `usbhid_disconnect()` only sets
  `HID_DISCONNECTED`.
- `i2c_hid_core_remove()` sequence:
  1. `drm_panel_remove_follower()` for a panel follower, otherwise
     `i2c_hid_core_suspend()`, which calls `disable_irq()` and powers down
     when `hid_driver_suspend()` succeeds.
  2. `hid_destroy_device()`.
  3. `free_irq()`.
  4. `i2c_hid_free_buffers()`.
- `i2c_hid_core_shutdown_tail()`: called only from `i2c_hid_core_shutdown()`,
  not on remove.
- Both orders of quiescing input exist: before destroy (`goodix_spi_remove()`
  calls `disable_irq()`), and inside destroy (`usbhid_stop()`).
- On teardown `->stop()` is reached only through `hid_hw_stop()`;
  `hid_device_remove()` calls `hid_hw_stop()` itself only when the bound driver
  has no `remove`.
- With no driver bound, `hid_destroy_device()` makes no `ll_driver` call.
- The guarantee after return has no single gate in the core; it rests on
  driver unbind in `device_del()`, `exist` cleared by `hidraw_disconnect()` and
  `hiddev_disconnect()`, and, under `CONFIG_HID_BPF`, `bpf.destroyed`.
- `bpf.destroyed`, under `CONFIG_HID_BPF`: makes
  `dispatch_hid_bpf_raw_requests()` and `dispatch_hid_bpf_output_report()`
  return `-ENODEV` before the `ll_driver` call, for every caller, including a
  HID-BPF context that outlives the device; without `CONFIG_HID_BPF` nothing
  sets it.
- `__hid_input_report()`: returns `-ENODEV` once `hid->driver` is NULL, so
  input arriving after the unbind is dropped, provided the memory is still
  there.
- **Potentially unsafe usage**: transport input path calling
  `hid_input_report()` after `hid_destroy_device()` returned.
  - Unsafe: when the transport holds only the allocation reference;
    `put_device()` may already have run `hiddev_free()`.
  - Safe: when the transport holds its own reference, as
    `hidp_session_dev_add()` takes with `get_device()`.
  - Safe: when the source is stopped before or inside destroy, as
    `goodix_spi_remove()` and `usbhid_stop()` do.
