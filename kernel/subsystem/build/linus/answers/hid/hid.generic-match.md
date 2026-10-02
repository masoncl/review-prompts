- `HID_QUIRK_HAVE_SPECIAL_DRIVER`: the only code that sets it is
  `hid_gets_squirk()` in `drivers/hid/hid-quirks.c`, from the
  `hid_have_special_driver` table; `hid_ignore()` and `hid_match_device()` do
  not read the table.
- Dynamic quirk entry for the device: `hid_lookup_quirk()` returns that entry
  alone and skips `hid_gets_squirk()`, so the table entry has no effect.
- Table entry, side effect: `hid_set_group()` skips `hid_scan_report()`, so
  with `hid_ignore_special_drivers` clear `hdev->group` stays 0 unless the
  transport set it. `hid_match_one_id()` then rejects any id entry whose
  `group` is not `HID_GROUP_ANY`.
- Dynamic id added through `new_id_store()`: only `driver_attach()` runs, and
  `__driver_probe_device()` returns `-EBUSY` for a bound device. A device
  already bound to hid-generic stays there; the reprobe walk runs only from
  `__hid_register_driver()`.
