- `hidraw_send_report()`: calls `__hid_hw_output_report()` only for
  `HID_OUTPUT_REPORT` on a device without
  `HID_QUIRK_NO_OUTPUT_REPORTS_ON_INTR_EP`; with the quirk it goes straight
  to `__hid_hw_raw_request()` with `HID_REQ_SET_REPORT`.
- `hidraw_send_report()` fallback test: `ret != -ENOSYS` on the return value;
  it does not look at the `output_report` pointer, and returns every other
  error unchanged.
- `-ENOSYS` does not prove the callback is absent: `usbhid_output_report()`
  returns it when `usbhid->urbout` is NULL, and
  `i2c_hid_set_or_send_report()` when `wMaxOutputLength` is 0.
- `hidinput_led_worker()`: calls `ll_driver->request` directly when the
  transport has one; only otherwise does it try `hid_hw_output_report()`,
  then `hid_hw_raw_request()` on `-ENOSYS`.
- `Documentation/hid/hid-transport.rst` says `output_report` must be
  asynchronous and that asynchronous calls work in atomic context; the code
  does not: `usbhid_output_report()` blocks in `usb_interrupt_msg()` and
  `i2c_hid_output_raw_report()` takes a mutex.
