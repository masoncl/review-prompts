- `->raw_event()`: called from `__hid_input_report()` before
  `hid_report_raw_event()`; with no HID-BPF program attached, `data` and
  `size` are as the transport delivered them. `size` is tested only for
  non-zero, not against the report length; the report may have
  `maxfield == 0`.
- Missing field: `hid_add_field()` returns 0 when `hid_register_field()`
  fails (allocation, or `HID_MAX_FIELDS` reached), so parsing succeeds with
  fewer fields than the descriptor has main items.
