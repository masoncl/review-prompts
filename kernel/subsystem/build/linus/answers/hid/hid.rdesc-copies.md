- `struct hid_device` holds three descriptor pointers, each with its own size
  field:

| Pointer | Set in | May equal | Freed in |
|---|---|---|---|
| `dev_rdesc` | `hid_parse_report()`, a `kmemdup()` of the transport's bytes | no earlier copy | `hid_remove_device()`, which also sets it NULL; `hiddev_free()` calls `kfree()` on it again, on NULL after `hid_remove_device()` |
| `bpf_rdesc` | `__hid_device_probe()`, from `call_hid_bpf_rdesc_fixup()` | `dev_rdesc`, when no HID-BPF rdesc program is attached or it fails; always without `CONFIG_HID_BPF` | `hid_free_bpf_rdesc()`, only if it differs from `dev_rdesc` |
| `rdesc` | `hid_open_report()` | `bpf_rdesc` (and through it `dev_rdesc`), only when the driver has no `report_fixup` | `hid_close_report()`, only if it differs from both `dev_rdesc` and `bpf_rdesc` |

- `rdesc` with a `report_fixup`: always a fresh `kmemdup()` owned by the
  core, also when the fixup returns its input unchanged.
- `rdesc` without a `report_fixup`: `hid_open_report()` makes no copy.
- `hid_close_report()`: never frees `dev_rdesc` or `bpf_rdesc`.
- `hid_free_bpf_rdesc()`: called from `__hid_device_probe()` before a
  recompute, from `hid_remove_device()` and from `hiddev_free()`.
