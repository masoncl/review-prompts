- There is no hidinput_app_is_shared helper here;
  `hidinput_match_application()` in `drivers/hid/hid-input.c` does the sharing.
- Shared under `HID_QUIRK_INPUT_PER_APP`: only `HID_GD_SYSTEM_CONTROL` and
  `HID_CP_CONSUMER_CONTROL` reports, and only into a `struct hid_input` whose
  `application` is `HID_GD_KEYBOARD`; vendor-defined applications are not.
- Order dependence: the keyboard test is made per list entry, so a keyboard
  input earlier on `hid->inputs` takes those reports even if an exact match
  sits later; with no keyboard input on the list yet they get their own.
- `HID_QUIRK_INPUT_PER_APP` with `hid->maxapplication <= 1` and without
  `HID_QUIRK_MULTI_INPUT`: no matching is done and no suffix added; all
  reports share one `struct hid_input`, as with neither quirk.
- Per-application key: `report->application`, set once by
  `hid_register_report()` from the application collection around the first
  main item of that report; every field of a report goes to the same input,
  whatever its `field->application`.
- `hidinput->application`: a driver may overwrite it during mapping, which
  changes what later reports match; `mt_input_mapping()` sets it to
  `HID_DG_STYLUS` for a field whose `physical` is `HID_DG_STYLUS`.
- Both quirks set: matching is by report id only, but `hidinput_allocate()`
  still records `application` and appends the per-application name suffix,
  since it tests only `HID_QUIRK_INPUT_PER_APP` and `hid->maxapplication > 1`.
