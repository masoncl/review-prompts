- `hiddev_free()` in `drivers/hid/hid-core.c`: the function that does
  `kfree()` of the `struct hid_device`; it is the kref release of `ref` and is
  unrelated to `struct hiddev` in `include/linux/hiddev.h`.
- `hid_device_release()`: frees nothing itself; it only does
  `kref_put(&hid->ref, hiddev_free)`.
- Two counts gate the free: the `struct device` refcount and `ref`; the memory
  goes when the device is released and every `ref` holder has dropped.
- `hid_destroy_device()`: calls `hid_bpf_destroy_device()`, then
  `hid_remove_device()`, then `put_device()`; it does not call `hiddev_free()`.
- `hid_remove_device()`: frees and NULLs `dev_rdesc` whether or not the device
  was added, so a later holder sees `dev_rdesc == NULL`.

| Holder after `hid_destroy_device()` returns | Holds | Dropped by |
|---|---|---|
| open debugfs `events` file (`CONFIG_DEBUG_FS`) | `ref`, via `hid_debug_events_open()` | `hid_debug_events_release()`, which may run `hiddev_free()` |
| HID-BPF context from `hid_bpf_allocate_context()` (`CONFIG_HID_BPF`) | device reference | `hid_bpf_release_context()` |
| `hid_haptic_init()` (`CONFIG_HID_HAPTIC`) | device reference | `hid_haptic_destroy()`, run from `input_dev_release()` |
| transport's own, for example `hidp_session_dev_add()` | device reference | the transport |

- HID-BPF struct_ops attachments (`hid_bpf_reg()`): their references are
  dropped inside `hid_destroy_device()` by `__hid_bpf_ops_destroy_device()`.
- Open hidraw and hiddev files: hold no reference on the `struct hid_device`;
  they keep `struct hidraw` or `struct hiddev` and test `exist`.
- Child devices: `device_del()` drops the reference on the parent, so an
  unregistered input or hidraw device no longer pins the hid device.
