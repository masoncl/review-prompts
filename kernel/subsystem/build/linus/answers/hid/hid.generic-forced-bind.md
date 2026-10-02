- `hid_check_device_match()`: returns `bool`. False for the specific driver
  becomes `-ENODEV` in `__hid_device_probe()`.
- `hid_generic_match()`: has no test of `hdev->group` of its own; the group
  counts only in `hid_match_device()`, which it calls for the other drivers.
- `HID_QUIRK_IGNORE_SPECIAL_DRIVER`: no table or driver in this tree sets it.
- HID-BPF programs cannot set it: `hid_bpf_ops_btf_struct_access()` in
  `drivers/hid/bpf/hid_bpf_struct_ops.c` allows writes to `name`, `uniq` and
  `phys` of `struct hid_device` only.
- Ways the bit reaches `hdev->quirks`: the dynamic quirk list filled by
  `hid_quirks_init()` (usbhid module parameter), or `hdev->initial_quirks`.
- `hid_ignore_special_drivers` set: `hid_set_group()` also forces
  `hdev->group` to `HID_GROUP_GENERIC` without scanning the descriptor.
