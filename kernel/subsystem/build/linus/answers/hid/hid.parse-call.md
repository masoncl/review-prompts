- Second call while `HID_STAT_PARSED` is set: `WARN_ON()` and `-EBUSY`; it
  does not return 0.
- No way to parse again inside one binding after a parse succeeded:
  `hid_close_report()` is static in `drivers/hid/hid-core.c`.
- Source descriptor: `hdev->bpf_rdesc` and `hdev->bpf_rsize`, not
  `hdev->dev_rdesc`. `__hid_device_probe()` sets them, so a call before the
  first probe hits `WARN_ON(!start)` and returns `-ENODEV`.
- On failure of `hid_parse_collections()`: `hid_open_report()` calls
  `hid_close_report()` itself before it returns the error; for what that
  frees and what stays for the next probe see "Report descriptor copies".
- **Unsafe usage**: calling `hid_hw_start()` after `hid_parse()` failed or was
  skipped. Nothing in `hid_hw_start()` tests `HID_STAT_PARSED`, and
  `usbhid_start()` dereferences `hid->collection`, which is NULL then.
  - Safe: return the error of `hid_parse()` first, as `hid_generic_probe()`
    does.
