- `parse` is called from one place, `hid_add_device()`, before `device_add()`;
  `hid_open_report()` and driver probe never call it.
- Success without `hid_parse_report()`: `hid_add_device()` finds
  `hdev->dev_rdesc` NULL and returns `-ENODEV`; no driver probe ever runs.
- `hid_parse_report()` called a second time: overwrites `hid->dev_rdesc`
  without freeing the earlier copy.
