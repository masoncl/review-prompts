- Return value: -1 on every failure, never an errno; `hid_connect()` only
  tests for non-zero.
- Decline test: scans `hid->collection[]`, not reports or usages, for an
  application or physical collection whose usage passes
  `IS_INPUT_APPLICATION()`.
- `hidinput_connect()` has no force argument; the test is
  `connect_mask & HID_CONNECT_HIDINPUT_FORCE` inside `hidinput_connect()`.
- Declined connect: returns before `report_features()`, so `feature_mapping`
  is never called for that device.
- `HID_CLAIMED_INPUT`: `hidinput_connect()` never writes `hid->claimed`;
  `hid_connect()` sets the bit on a zero return and has nothing to clear on
  failure.
- Empty test: `hidinput_has_been_populated()` ORs nine bitmaps, not just
  `evbit`; `propbit` is not among them.
- Order: `input_configured` runs before the empty test, so a non-zero return
  on an empty input still aborts the whole connect.
- All inputs dropped as empty: `hid->inputs` is empty, so the connect goes to
  `out_unwind` and returns -1.
- `hidinput_cleanup_hidinput()`: resets `field->hidinput` to NULL on matching
  fields; does not unlink `report->hidinput_list` from the freed
  `hidinput->reports`.
- `hidinput_disconnect()`: does not reset `field->hidinput`, and does not undo
  `report_features()`.
- Batteries: not cleaned by `hidinput_disconnect()`;
  `hidinput_setup_battery()` registers them as devres on `hid->dev`, so they
  outlive the unwind.
- `hid->ff_init()`: called inside the registration loop under
  `HID_CONNECT_FF`; its return value is ignored and cannot fail the connect.
