- `__hid_hw_raw_request()` checks only `len >= 1`, `len <= max_buffer_size`
  and `buf != NULL`; it does not test that `raw_request` exists and does not
  look at `reportnum`.
- `rtype` under `CONFIG_HID_BPF`: `dispatch_hid_bpf_raw_requests()` returns
  `-EINVAL` for `rtype >= HID_REPORT_TYPES`, and `-ENODEV` when
  `hdev->bpf.destroyed`.
- `rtype` without `CONFIG_HID_BPF`: the stub in `include/linux/hid_bpf.h`
  returns 0, so the core does not test `rtype`; `uhid_hid_raw_request()`
  tests it itself.
- Unknown `reqtype`: `-EIO` in, for example, `usbhid_raw_request()` and
  `i2c_hid_raw_request()`; not every transport does so,
  `goodix_hid_raw_request()` returns `-EINVAL`.
- `usbhid_raw_request()`: dispatches to `usbhid_get_raw_report()` and
  `usbhid_set_raw_report()`; there is no hid_get_class_report() or
  hid_set_class_report() here.
- `usbhid_set_raw_report()`: sends every report type, output included, with
  `usb_control_msg()`; it never uses the interrupt OUT endpoint.
- `buf` is not checked for DMA capability: usbhid passes it to
  `usb_control_msg()` without copying, and on a host controller that uses
  DMA `usb_hcd_map_urb_for_dma()` fails an on-stack transfer buffer with
  `-EAGAIN`; `hid_bpf_hw_request()` copies into a `kmemdup()` buffer before
  the call.
