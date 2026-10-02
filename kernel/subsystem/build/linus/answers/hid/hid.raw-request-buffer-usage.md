- Maximum length: `hdev->ll_driver->max_buffer_size` when it is non-zero,
  otherwise `HID_MAX_BUFFER_SIZE`; see `__hid_hw_raw_request()` and
  `__hid_hw_output_report()` in `drivers/hid/hid-core.c`.
- uhid: sets `max_buffer_size` to `UHID_DATA_MAX`, so the core rejects a longer
  buffer there with `-EINVAL`; it is the only transport that sets the field.
- `hid_hw_output_report()` with a NULL `buf`: rejected with `-EINVAL`, by the
  same test as in `hid_hw_raw_request()` (`len < 1`, `len` above the maximum,
  or `!buf`).
- **Unsafe usage**: passing `const` or read-only data as the buffer of a
  SET_REPORT.
  - Safe: copy the template with `kmemdup()` and free it after the call, as
    `kysona_m600_fetch_online()` in `drivers/hid/hid-kysona.c` does;
    `usbhid_set_raw_report()` and `hidp_set_raw_report()` write byte 0 of
    the buffer.
- Length for report id 0: must count the reserved byte 0; see "Report id
  byte".
