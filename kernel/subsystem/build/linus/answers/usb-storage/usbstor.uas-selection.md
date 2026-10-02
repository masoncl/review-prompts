- Nonzero result of `uas_use_uas_driver()`: `storage_probe()`, which makes the
  call only under `IS_ENABLED(CONFIG_USB_UAS)`, returns `-ENXIO` without
  checking that uas is loaded; `uas_probe()` can still fail afterwards, for
  example in `uas_switch_interface()`. At most one of the two binds, not
  exactly one.
- uas has no module parameter of its own; the usb-storage `quirks` string
  reaches it through `usb_stor_adjust_quirks()`.
- The function returns 0 in these cases, tested in this order:
  1. no altsetting passes `uas_is_interface()` (code)
  2. `uas_find_endpoints()` does not find all four pipe-usage descriptors
     (code)
  3. `US_FL_IGNORE_UAS` is set after `usb_stor_adjust_quirks()` (table,
     `quirks` letter `u`, or the coded cases below)
  4. `udev->bus->sg_tablesize == 0` (code)
  5. speed is `USB_SPEED_SUPER` or above and `hcd->can_do_streams` is 0
     (code)
- Coded cases that set flags, all before `usb_stor_adjust_quirks()`:
  - ASMedia 174c:5106 and 174c:55aa with `bMaxPower != 0`: below
    `USB_SPEED_SUPER`, or exactly 32 streams on the status pipe, sets
    `US_FL_IGNORE_UAS`; any other stream count sets `US_FL_MAX_SECTORS_240`.
  - Vendor 0x0bc2: sets `US_FL_NO_ATA_1X`; uas still binds.
  - 0bda:9210 with manufacturer "HIKSEMI" and product "MD202": sets
    `US_FL_IGNORE_UAS`.
  - No VIA device is coded in the function.
- Flags the function adds in code reach uas only: `storage_probe()` passes
  `NULL` for `flags_ret`, and `get_device_info()` builds `us->fflags` from
  `id->driver_info` plus `quirks`.
- `drivers/usb/storage/unusual_uas.h` is included in two places:
  - `drivers/usb/storage/uas.c`, inside `uas_usb_ids[]`.
  - `drivers/usb/storage/unusual_devs.h`, under
    `#if IS_ENABLED(CONFIG_USB_UAS)`, after the last `UNUSUAL_DEV()` entry and
    before the `USUAL_DEV()` entries.
- `drivers/usb/storage/unusual_uas.h` is not included in
  `drivers/usb/storage/uas-detect.h`, nor directly in
  `drivers/usb/storage/usb.c`.
- `usb_match_id()` returns the first match: a device that matches an entry in
  both files gets the `drivers/usb/storage/unusual_devs.h` flags in
  `storage_probe()` and the `drivers/usb/storage/unusual_uas.h` flags in
  `uas_probe()`.
- An entry in `drivers/usb/storage/unusual_devs.h` outside
  `drivers/usb/storage/unusual_uas.h` is not in `uas_usb_ids[]`;
  `uas_probe()` matches such a device through a generic interface entry with
  `driver_info` 0, so the two calls of the function can return different
  results.
