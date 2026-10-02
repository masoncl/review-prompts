- `hid_hw_request()` without `->request`: falls back to `__hid_request()` in
  `drivers/hid/hid-core.c`, which allocates with `GFP_KERNEL` and returns only
  after `hid_hw_raw_request()` did; the return value of `__hid_request()` is
  discarded.
- `__hid_request()`: sends through `hid_hw_raw_request()`, not the transport
  callback directly, so the length checks and the HID-BPF hook apply to it.
- `hid_hw_request()` on usbhid: `__usbhid_submit_report()` uses the interrupt
  OUT queue only for a SET of a `HID_OUTPUT_REPORT` when `usbhid->urbout`
  exists; every other `HID_REQ_GET_REPORT` or `HID_REQ_SET_REPORT` goes on
  the control queue.
- `usbhid_request()` drops the request with no error to the caller when: the
  queue is full, the `GFP_ATOMIC` allocation fails, `HID_DISCONNECTED` is set,
  or the request is a GET and the device has `HID_QUIRK_NOGET`.
- `hid_hw_output_report()` waiting is transport-dependent:
  `usbhid_output_report()` waits for the transfer; `hidp_output_report()` and
  `uhid_hid_output_raw()` queue the data and return the count at once.
- `__hid_hw_output_report()` order: length check, then the HID-BPF hook, then
  the test for a NULL `->output_report`.
