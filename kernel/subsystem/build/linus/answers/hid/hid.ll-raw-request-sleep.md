- `usbhid_raw_request()` never calls `usb_interrupt_msg()`; its get and set
  paths both block in `usb_control_msg()`.
- `hid_hw_raw_request()` kerneldoc states no calling context; the transports
  are the evidence, for example `uhid_hid_get_report()` with
  `mutex_lock_interruptible()` and, in `__uhid_report_queue_and_wait()`,
  `wait_event_interruptible_timeout()`.
