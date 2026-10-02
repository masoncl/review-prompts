- `HID_CONNECT_HIDDEV` on USB: added only by `HID_QUIRK_HIDDEV_FORCE`;
  otherwise it must be in the mask.
- `hdev->bus != BUS_USB`: clears `HID_CONNECT_HIDDEV` after the quirk test, so
  `HID_QUIRK_HIDDEV_FORCE` cannot connect hiddev on another bus.
- `hdev->hiddev_connect`: set only by `usbhid_probe()`, under
  `CONFIG_USB_HIDDEV`.
- Failure for lack of listeners: `-ENODEV` with "device has no listeners,
  quitting", only when `hdev->claimed` is 0 and the driver has no `raw_event`.
- Failed `hidinput_connect()`, `hidraw_connect()` or `hiddev_connect`: not an
  error for `hid_connect()`; the claimed bit just stays clear.
- `HID_CONNECT_DRIVER`, second effect: `hid_report_raw_event()` skips
  `hid_process_report()` and the `report` callback when `hdev->claimed` equals
  `HID_CLAIMED_HIDRAW`. With `HID_CLAIMED_DRIVER` also set, a hidraw-only
  device gets `event` and `report`; `udraw_probe()` in
  `drivers/hid/hid-udraw-ps3.c` passes that mask.
- `HID_CONNECT_HIDINPUT_FORCE`: skips only the test for a collection of type
  `HID_COLLECTION_APPLICATION` or `HID_COLLECTION_PHYSICAL` whose usage
  satisfies `IS_INPUT_APPLICATION()`.
- With force, an input device that `hidinput_has_been_populated()` rejects is
  still dropped, and `hidinput_connect()` fails when no input is left.
- `HID_CONNECT_FF`: read inside `hidinput_connect()`, which calls
  `hid->ff_init` before it registers the first input device; `hid_connect()`
  itself does not call `ff_init`.
