- `hdev->quirks` is assigned from `hid_lookup_quirk()` in two places:
  `hid_add_device()` and `__hid_device_probe()`, the second on every bind.
- `usbhid_parse()` is the third caller of `hid_lookup_quirk()`;
  `hid_ignore()` and `hid_quirks_init()` do not call it.
- Reset position in `__hid_device_probe()`: after
  `hid_check_device_match()`, so `->match()` and the
  `HID_QUIRK_IGNORE_SPECIAL_DRIVER` test see the value left by
  `hid_add_device()` or by the previous driver.
- Reset and the default probe: the reset also runs when the driver has no
  `->probe()`.
- No hid_set_quirk() helper exists; drivers write `hdev->quirks |= ...`.
- `hid_open_report()` and the parser in `drivers/hid/hid-core.c`: test no
  bit of `hdev->quirks`, so the core imposes no order relative to
  `hid_parse()`.
- Bits set between `hid_parse()` and `hid_hw_start()`: have the same effect
  as bits set before `hid_parse()`, as `HID_QUIRK_NOGET` in `mt_probe()` and
  `HID_QUIRK_INPUT_PER_APP` in `logi_dj_probe()`.
- `HID_QUIRK_INCREMENT_USAGE_ON_DUPLICATE`: tested in
  `hidinput_configure_usage()` during `hid_connect()`, not while parsing.
- HID_QUIRK_NO_EMPTY_INPUT: not defined; bit 8 is reserved in
  `include/linux/hid.h`.
- HID-BPF: nothing under `drivers/hid/bpf` names `quirks`; in
  `__hid_device_probe()` the rdesc fixup and `hid_set_group()` run before the
  reset.
- **Unsafe usage**: relying, in a bound driver, on a bit ORed into
  `hdev->quirks` before the bind, for example from `ll_driver->parse()`;
  the assignment in `__hid_device_probe()` drops every bit the lookup does
  not return.
  - Safe: set `hdev->initial_quirks` before `hid_add_device()`, as
    `i2c_hid_core_probe()` does; `hid_gets_squirk()` starts every lookup
    from it when no early return or dynamic entry applies.
  - Safe: set the bit in `->probe()`, after the reset, as
    `hid_generic_probe()` does.
- **Potentially unsafe usage**: setting a bit once `hid_hw_start()` has
  been called.
  - Unsafe: when the bit is tested once during start or connect, such as
    `HID_QUIRK_FULLSPEED_INTERVAL` in `usbhid_start()` or
    `HID_QUIRK_MULTI_INPUT` in `hidinput_connect()`.
  - Safe: when the bit is tested on each transfer, as
    `HID_QUIRK_SKIP_OUTPUT_REPORT_ID` in `usbhid_set_raw_report()` and
    `HID_QUIRK_NO_OUTPUT_REPORTS_ON_INTR_EP` in `hidraw_send_report()`;
    `sony_input_configured()` sets both during `hid_connect()`.
