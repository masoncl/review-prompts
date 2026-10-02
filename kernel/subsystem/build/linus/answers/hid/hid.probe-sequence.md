- `driver_input_lock`: a `struct semaphore`, initialised to 1 in
  `hid_allocate_device()`. There is no ll_driver_lock in this tree.
- First step of `__hid_device_probe()`, when `hdev->bpf_rsize` is 0:
  `call_hid_bpf_rdesc_fixup()` fills `hdev->bpf_rdesc` and `hdev->bpf_rsize`.
  If the descriptor changed, `hdev->group` is recomputed by `hid_set_group()`.
  This runs before the match check.
- Without `CONFIG_HID_BPF`: `call_hid_bpf_rdesc_fixup()` returns its argument,
  so `hdev->bpf_rdesc` is `hdev->dev_rdesc`.
- `hdev->quirks = hid_lookup_quirk(hdev)`: runs on every probe, after the
  match check and after the devres group is opened, just before
  `hdev->driver` is set.
