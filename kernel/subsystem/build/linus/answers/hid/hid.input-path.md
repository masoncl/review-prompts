- `raw_event`: runs before the size check; hiddev and then hidraw run after
  it, inside `hid_report_raw_event()`.
- Field parsing, `event` and `report`: gated by
  `hid->claimed != HID_CLAIMED_HIDRAW && report->maxfield`, not by
  `HID_CLAIMED_INPUT`.
- `HID_CLAIMED_INPUT`: gates only `hidinput_hid_event()` inside
  `hid_process_event()` and the final `hidinput_report_event()`.
- There is no hid_input_field() here; `hid_process_report()` calls
  `hid_input_fetch_field()` for every field first, then dispatches usages.
- `hid_process_report()` with a non-empty `report->field_entry_list`: walks
  that list, so `event` calls do not follow field index order.
- `report_table`: a driver filter in `struct hid_driver`, matched by
  `hid_match_report()` on report type only, never on report id; gates only
  `raw_event`.
- `usage_table`: a driver filter matched by `hid_match_usage()` on
  `usage_hid`, `usage_type` and `usage_code`; gates only `event`; a usage
  that fails still goes to `hidinput_hid_event()`.
