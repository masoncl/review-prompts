- Models take `hid_report_raw_event()` to take `size` only. It takes
  `bufsize` then `size`; drivers that call it directly pass six arguments, as
  in `drivers/hid/wacom_sys.c`.
- Models take `hid_hw_open()` and `hid_hw_close()` to call only the
  transport. On the first open and last close they also call the driver's
  `on_hid_hw_open` or `on_hid_hw_close`, under `ll_open_lock`, and
  dereference `hdev->driver` to do so. See `drivers/hid/hid-multitouch.c`.
- Models take `HID_CONNECT_FF` to always reach `ff_init`.
  `hidinput_connect()` skips the call when `hid_has_ff_input()` finds `EV_FF`
  already set on an input device on `hdev->inputs`.
- Models take a device to have one battery. `hid_get_battery()` in
  `include/linux/hid.h`, defined only under `CONFIG_HID_BATTERY_STRENGTH`,
  returns only the first `struct hid_battery` on `hdev->batteries`, or NULL
  when the list is empty.
- Models do not know `kzalloc_obj()`, `kzalloc_objs()` and `kmalloc_obj()`,
  used across `drivers/hid/`. They are in `include/linux/slab.h` and default to
  `GFP_KERNEL` when no flags are given.
