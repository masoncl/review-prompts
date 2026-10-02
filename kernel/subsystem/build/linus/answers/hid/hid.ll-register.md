- `name`, `uniq`, `type`, `version`: not only informational; `hid_ignore()`
  matches on `name`, `uniq` and `type`, `hid_lookup_quirk()` on `version`, both
  in `hid_add_device()` before `->parse()` runs.
- `ll_driver`: the only pointer field of `struct hid_device` that
  `hid_add_device()` dereferences with no NULL test; the other fields a
  transport sets start zeroed in `hid_allocate_device()`, and for example
  `goodix_hid_init()` sets neither `phys` nor `uniq`.
- **Potentially unsafe usage**: calling `hid_add_device()` from the context
  that services the transport's I/O, or under a lock its callbacks take.
  - Unsafe: when a HID driver's probe, run synchronously inside `device_add()`,
    blocks in `->raw_request()` waiting on that context.
  - Safe: from a work item, as `uhid_device_add_worker()` and
    `hidp_session_dev_work()` do; `uhid_char_write()` holds `devlock` and
    delivers the reply that `uhid_hid_get_report()` waits for.
  - Safe: from bus probe when callbacks complete on their own, as
    `usbhid_probe()` does; `usbhid_raw_request()` blocks only in
    `usb_control_msg()`.
