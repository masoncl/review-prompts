- `hid_lookup_quirk()` order: two hard-coded early returns, then the dynamic
  list, then `hid_gets_squirk()` only if no dynamic entry matched.
- Early returns consult no table and return one bit alone: USB NCR product
  range gives `HID_QUIRK_NO_INIT_REPORTS`; USB Jabra Speak 410/510 with
  `hdev->version` below a threshold gives `HID_QUIRK_IGNORE`.
- Dynamic match: the entry's `driver_data` is the whole result; it replaces.
- `hid_gets_squirk()`: adds. It ORs `hdev->initial_quirks`,
  `hid_ignore_list` (`HID_QUIRK_IGNORE`), `hid_mouse_ignore_list`
  (`HID_QUIRK_IGNORE_MOUSE`), `hid_have_special_driver`
  (`HID_QUIRK_HAVE_SPECIAL_DRIVER`) and the `hid_quirks[]` entry.
- `hdev->initial_quirks`: is the start value inside `hid_gets_squirk()`; no
  caller ORs it in. An early return or a dynamic match leaves it out.
- `initial_quirks` writers: only `i2c_hid_core_probe()` and
  `__i2c_hid_core_probe()` in `drivers/hid/i2c-hid/i2c-hid-core.c`. There is
  no usbhid_quirks_init() function.
- Dynamic entries: come from the `quirks` parameter of usbhid, not of hid;
  `hid_quirks_init()` is called only from `drivers/hid/usbhid/hid-core.c`
  with `BUS_USB`.
- Dynamic entries and `initial_quirks` together: no in-tree device has both,
  since dynamic entries match only `BUS_USB` and `initial_quirks` is set only
  on `BUS_I2C` devices.
- `hid_ignore_list` is matched twice: as a bit in `hid_gets_squirk()`, and
  directly on the last line of `hid_ignore()`, even when `HID_QUIRK_IGNORE`
  is clear.
- Direct match in `hid_ignore()`: a listed device stays ignored when a
  dynamic entry replaced the static result, and when `hid_ignore()` runs
  before any lookup, as in `hidp_setup_hid()` in `net/bluetooth/hidp/core.c`.
- `HID_QUIRK_NO_IGNORE`: the only override, tested first in `hid_ignore()`;
  nothing in the tree sets it, so only a dynamic entry can supply it.
- `hid_mouse_ignore_list`: `hid_ignore()` tests only the bit
  `HID_QUIRK_IGNORE_MOUSE`, not the list, so a dynamic entry without that bit
  un-ignores the mouse interface.
- Product ranges and name-based ignores: code in the `switch` of
  `hid_ignore()`, not entries of `hid_ignore_list`.
