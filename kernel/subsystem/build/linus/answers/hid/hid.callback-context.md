- There is no driver_lock field in `struct hid_device`;
  `driver_input_lock` is the only lock `__hid_input_report()` takes around
  the callbacks.
- `hid_report_raw_event()` called directly: does not take
  `driver_input_lock`, and still calls `event` and `report`; the caller
  provides the exclusion, for example `gfrm_raw_event()` (already inside
  `raw_event`) or `asus_kbd_wmi_fan()` (explicit `down()`).
- **Potentially unsafe usage**: calling `hid_hw_request()` from `raw_event`,
  `event` or `report`.
  - Unsafe: on a transport that delivers input in atomic context and whose
    `struct hid_ll_driver` has no `request`, for example a child device of
    `drivers/hid/hid-logitech-dj.c` (`logi_dj_ll_driver`, fed under a
    spinlock by `logi_dj_dj_event()`); `hid_hw_request()` falls back to
    `__hid_request()`, which allocates with `GFP_KERNEL` and calls
    `hid_hw_raw_request()`.
  - Safe: on usbhid, where `request` is `usbhid_request()`; it queues under
    `usbhid->lock` and allocates with `GFP_ATOMIC`, as `pk_raw_event()` in
    `drivers/hid/hid-prodikeys.c` relies on after `pk_probe()` tested
    `hid_is_usb()`.
