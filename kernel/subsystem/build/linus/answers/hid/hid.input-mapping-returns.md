- Before any callback: `hidinput_configure_usage()` goes to `ignore` without
  calling `input_mapping` for `HID_MAIN_ITEM_CONSTANT` fields, for
  `report_count < 1`, and for output-report usages outside `HID_UP_LED` and
  `HID_UP_HAPTIC`.
- `ignore` versus plain `return`: only `ignore` zeroes `usage->type` and
  `usage->code`; the two early returns at `mapped` leave them as written.
- `input_mapped` < 0: plain `return`, not `ignore`; `usage->type` and
  `usage->code` keep the mapping, the core does not set `usage->type` in
  `input->evbit` or `usage->code` in `*bit`, and no duplicate check runs.
- `input_mapped` is not called when `bit` is NULL at `mapped`, nor for a usage
  that went to `ignore`.
- Positive `input_mapping` with `*bit` left NULL: the generic switch is
  skipped and the core touches neither the usage nor the input device; this is
  how a driver claims a usage it handles itself, for example
  `mt_touch_input_mapping()` in `drivers/hid/hid-multitouch.c` for
  `HID_DG_CONTACTID`.
- `hid_map_usage()` failure: writes only `*bit = NULL`; `usage->type`,
  `usage->code` and `*max` keep their previous values.
- `hid_map_usage()` accepted types: `EV_ABS`, `EV_REL`, `EV_KEY`, `EV_LED`,
  `EV_MSC`; any other type, for example `EV_SW`, fails.
- **Potentially unsafe usage**: setting the code's bit in the input bitmap by
  hand, then returning positive from `input_mapping` with `*bit` non-NULL.
  - Unsafe: when `input_mapped` is absent or returns >= 0 for that usage; the
    `test_and_set_bit()` in `hidinput_configure_usage()` sees a duplicate and,
    without `HID_QUIRK_INCREMENT_USAGE_ON_DUPLICATE`, sets
    `HID_STAT_DUP_DETECTED` and zeroes `usage->type` and `usage->code`, while
    the capability bit stays set.
  - Safe: when `input_mapped` returns negative for the same usage, so the
    duplicate check never runs, as `mt_touch_input_mapping()` with
    `mt_input_mapped()` does for buttons.
  - Safe: map with `hid_map_usage_clear()` and let the core set the bit, as
    `ch_input_mapping()` in `drivers/hid/hid-chicony.c` does; the cleared bit
    makes the `test_and_set_bit()` in `hidinput_configure_usage()` return 0.
