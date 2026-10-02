- `hid_parse_report()` and `hid_open_report()`: test no size before the fixup
  runs, neither a minimum nor `HID_MAX_DESCRIPTOR_SIZE`.
- Zero-length and `HID_MAX_DESCRIPTOR_SIZE` tests: in individual transports,
  for example `usbhid_parse()` and `i2c_hid_parse()`; search for
  `HID_MAX_DESCRIPTOR_SIZE` to see which, since others call
  `hid_parse_report()` with no such test, for example `surface_hid_parse()`.
- Bytes passed to the fixup: a copy of `bpf_rdesc`, so the output of a HID-BPF
  program when one is attached, not always the device's bytes.
- Returned `*size`: the core checks it against nothing but zero;
  `hid_parse_collections()` returns `-EINVAL` for a 0-sized descriptor.
- Returned `*size` larger than the returned buffer: the `kmemdup()` in
  `hid_open_report()` reads past its end.
