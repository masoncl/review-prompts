- `hid_add_device()` calls `ll_driver->parse()`, not `hid_parse_report()`;
  before `device_add()` it calls neither `hid_open_report()` nor any HID-BPF
  hook.
- Order of the failing checks: `HID_STAT_ADDED` (`-EBUSY`), `hid_ignore()`
  (`-ENODEV`), missing `->raw_request` (`-EINVAL`), `->parse()` (its return
  value), `dev_rdesc` still NULL (`-ENODEV`).
- `hid_scan_report()` failure: `hid_set_group()` only prints `hid_warn()`;
  registration continues.
- `-ENODEV` reaches the transport from several places it cannot tell apart:
  `hid_ignore()`, the `dev_rdesc` check, and `->parse()` itself, for example
  `usbhid_parse()`.
- Suppressing the log for `-ENODEV`: see `usbhid_probe()` and
  `i2c_hid_core_register_hid()`; this also hides the `dev_rdesc` and
  `->parse()` cases.
- HID driver probe failure: does not fail `hid_add_device()`; every error path
  of `device_add()` precedes `bus_probe_device()`.
