- `hid_bpf_reg()` in `drivers/hid/bpf/hid_bpf_struct_ops.c` refuses, in this
  order:

  | Condition | Error |
  |---|---|
  | `ops->hdev` already set (same struct_ops attached twice) | `-EINVAL` |
  | `hid_get_device()` finds no device with that `hdev->id`, or `hid_ops` is NULL | `-EINVAL` |
  | `hdev->bpf.prog_list` already holds `HID_BPF_MAX_PROGS_PER_DEV` ops | `-E2BIG` |
  | ops has `hid_rdesc_fixup` and `hdev->bpf.rdesc_ops` is already set | `-EINVAL` |
  | ops has `hid_device_event` and `hid_bpf_allocate_event_data()` fails | `-ENOMEM` |

- `hid_bpf_reg()` returns neither `-EEXIST` nor `-ENODEV`.
- `hdev->bpf.destroyed`: `hid_bpf_reg()` does not test it.
- `hid_rdesc_fixup` is the only hook `hid_bpf_reg()` limits to one per
  device.
- Unknown bits in `flags`: refused with `-EINVAL` by
  `hid_bpf_ops_init_member()` when the map value is written, before
  `hid_bpf_reg()` runs; `hid_bpf_reg()` only tests `BPF_F_BEFORE`.
- `hid_bpf_attach_prog()`: only an `extern` declaration in
  `samples/hid/hid_bpf_helpers.h`; nothing defines it, and the samples attach
  with `bpf_map__attach_struct_ops()`.
