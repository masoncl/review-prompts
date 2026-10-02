- `hid_add_device()`: builds no reports itself; it calls `ll_driver->parse()`,
  which stores the device bytes in `dev_rdesc`, then `hid_set_group()`, then
  `device_add()`.
- Report/field/usage tree: built by `hid_open_report()` (`hid_parse()` is the
  same call), from the driver's `probe`; `__hid_device_probe()` calls it
  itself, then `hid_hw_start()` with `HID_CONNECT_DEFAULT`, when the driver
  has no `probe`.
- `hdev->rdesc`: the descriptor that `hid_parse_collections()` parses; for the
  three descriptor pointers see "Report descriptor copies".
- Descriptor is walked twice: `hid_scan_report()` runs before binding and only
  sets `hdev->group`, which is part of the match key; it is skipped when the
  transport already set `group`, `HID_QUIRK_HAVE_SPECIAL_DRIVER` is set, or
  `hid_ignore_special_drivers` is set.
- `struct hid_parser`: used by both passes, `hid_scan_report()` and
  `hid_parse_collections()`.
- Attaching or detaching a HID-BPF `hid_rdesc_fixup` program: reprobes the
  device, see `hid_bpf_reconnect()` in `drivers/hid/bpf/hid_bpf_dispatch.c`;
  the whole parsed tree is rebuilt.
- HID-BPF lives in `drivers/hid/bpf/`. `struct hid_bpf_ops` is one attached
  program set (a BPF struct_ops), `struct hid_bpf` is the per-device state at
  `hdev->bpf`, `struct hid_ops` is the table through which the BPF side calls
  back into the core.
- Input path, in order; there is no hid_input_field() here:
  1. `hid_input_report()` or `hid_safe_input_report()`; the second also
     passes the allocated buffer size.
  2. `__hid_input_report()`: `dispatch_hid_bpf_device_event()`, which may
     return a different buffer.
  3. The driver's `raw_event`.
  4. `hid_report_raw_event()`: hiddev and hidraw get the report, so hidraw
     sees bytes already changed by BPF and by `raw_event`.
  5. `hid_process_report()`, then per usage `hid_process_event()`: the
     driver's `event`, then `hidinput_hid_event()` and hiddev.
  6. The driver's `report`, then `hidinput_report_event()`.
- `struct hid_field_entry`: one (field, usage index) slot in
  `report->field_entry_list`. After `hid_connect()`, input reports deliver
  variable usages in that list's priority order, which can differ from
  descriptor order; priorities come from `hidinput_configure_usage()`.
- `struct hid_usage`, not `struct hid_field`, holds the collection index
  (`collection_index`). The field holds copies of the enclosing application,
  physical and logical usages.
- `field->hidinput`: the link the event path follows to a
  `struct input_dev`; `hidinput_hid_event()` sends to
  `field->hidinput->input`. For when it is set and when it is NULL see
  "Inputs list and hidinput pointers".
- `hidinput->report`: set only under `HID_QUIRK_MULTI_INPUT`. With or without
  the quirk, reports hang on `hidinput->reports` through
  `report->hidinput_list`.
- `struct hid_battery`: one power supply per report id that carries a battery
  usage, on the list `hdev->batteries`, under `CONFIG_HID_BATTERY_STRENGTH`.
  There is no single battery field in `struct hid_device`.
- HID drivers that are also transports for child devices: they call
  `hid_allocate_device()` and supply a `struct hid_ll_driver`, for example
  `drivers/hid/hid-logitech-dj.c` and `drivers/hid/hid-steam.c`.
  `drivers/hid/hid-multitouch.c` and `drivers/hid/wacom_sys.c` do not call
  `hid_allocate_device()`.
