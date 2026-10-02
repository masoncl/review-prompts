- `hid_report_len()`: counts the id byte only when `report->id > 0`; for
  report id 0 it is the payload size alone.
- `hid_alloc_report_buf()`: allocates `hid_report_len()` + 7, plus 1 more byte
  when `report->id == 0`, so the caller can reserve byte 0.
- `__hid_request()` with `report->id == 0`: leaves byte 0 zero, fills the
  payload from byte 1 for a SET, and passes `hid_report_len()` + 1 as the
  length.
- Input path: the id byte is present when `report_enum->numbered` is set, and
  that flag is per report type; `hid_register_report()` sets it as soon as one
  report of that type has a non-zero id.
- `raw_event`: gets the same `data` and `size` as the core, id byte included
  for a numbered type; the byte is skipped only later, in
  `hid_report_raw_event()`.
- `hid_hw_raw_request()` buffer: byte 0 is the report id slot for every report,
  0 for report id 0, and `len` counts it.
- Byte 0 of a SET buffer: `usbhid_set_raw_report()` and
  `hidp_set_raw_report()` overwrite it with `reportnum`;
  `i2c_hid_raw_request()` returns `-EINVAL` when `buf[0] != reportnum`.
- `HID_QUIRK_SKIP_OUTPUT_REPORT_ID`: makes `usbhid_set_raw_report()` zero
  byte 0 of an output report, so the id byte is not sent.
- usbhid with report id 0: the skip of byte 0 is in `usbhid_get_raw_report()`
  and `usbhid_set_raw_report()`, not in `usbhid_raw_request()`; the returned
  count includes the skipped byte.
- `hid_hw_output_report()` buffer: has no report number argument; byte 0 is
  the id slot: `usbhid_output_report()` skips it when it is 0, and
  `i2c_hid_output_raw_report()` takes the id from it and always strips it.
- **Potentially unsafe usage**: filling a buffer with `hid_output_report()` at
  offset 0 and passing it with `hid_report_len()` to `hid_hw_raw_request()` or
  `hid_hw_output_report()`.
  - Unsafe: when `report->id == 0`; byte 0 then holds payload, which the
    transport overwrites or strips as the id, and the length is one short.
  - Safe: when `report->id > 0`; `hid_output_report()` puts the id in byte 0
    and `hid_report_len()` counts it.
  - Safe: for id 0, fill from byte 1 and pass the length plus 1, as
    `__hid_request()` does for SET; `usbhid_set_raw_report()` then skips
    byte 0.
  - Safe: for a GET of id 0, pass the length plus 1 and skip byte 0 of the
    reply before giving it to `hid_report_raw_event()`, as
    `vivaldi_feature_mapping()` in `drivers/hid/hid-vivaldi-common.c` does;
    `usbhid_get_raw_report()` stores the reply from byte 1.
