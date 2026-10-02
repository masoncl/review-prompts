- Open during probe: does not deliver reports to the driver by itself;
  `driver_input_lock` still drops them until `hid_device_io_start()` or the
  return of probe.
- I2C while closed: the interrupt is live; `i2c_hid_get_input()` reads the
  report from the device and drops it unless `I2C_HID_STARTED` is set.
- USB while closed, with `HID_QUIRK_ALWAYS_POLL`: `usbhid_start()` submits the
  interrupt-in URB, but `hid_irq_in()` discards the data while `HID_OPENED` is
  clear.
- USB control-pipe replies: `hid_ctrl()` passes them to
  `hid_safe_input_report()` without testing `HID_OPENED`, so a reply to
  `HID_REQ_GET_REPORT` arrives even with the device closed.
- `ll_open_count`: written only by `hid_hw_open()` and `hid_hw_close()`. The
  core never resets it, so a missing `hid_hw_close()` carries over into the
  next binding, whose first open then skips `ll_driver->open`.
- Drivers that open in probe and close in `remove`: for example
  `logi_dj_probe()`, `ps_probe()`, `cp2112_probe()`.
- `hidpp_probe()`: opens for the duration of probe only and calls
  `hid_hw_close()` before it returns.
