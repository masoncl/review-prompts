- In-tree examples: `usbhid_probe()` with `usbhid_disconnect()`, and
  `quicki2c_hid_probe()` with `quicki2c_hid_remove()`.
- Failed `hid_add_device()`: no HID driver was probed, and
  `hid_destroy_device()` on a never-added device makes no `ll_driver` call;
  that is why `usbhid_probe()` may `kfree()` its private data first.
- Clearing the transport's copy of the pointer: not needed by the core;
  `usbhid_disconnect()` and `i2c_hid_core_remove()` leave it set.
- `uhid_dev_destroy()` clears `uhid->hid` because `uhid_dev_create2()` tests it.
- **Unsafe usage**: calling `hid_destroy_device()` twice on one allocation;
  `put_device()` drops a reference each time, and under `CONFIG_HID_BPF`
  `hid_bpf_destroy_device()` runs `cleanup_srcu_struct()` each time.
  - Safe: one call per allocation, guarded by the transport's own pointer, as
    `uhid_dev_destroy()` does.
- **Unsafe usage**: `hid_destroy_device()` while a work item that calls
  `hid_add_device()` may still run; `HID_STAT_ADDED` is set and tested with no
  lock.
  - Safe: `cancel_work_sync()` first, as `uhid_dev_destroy()` and
    `hidp_session_remove()` do.
- **Potentially unsafe usage**: `put_device(&hid->dev)` by a transport, or use
  of the device after `hid_destroy_device()`.
  - Unsafe: when it drops or relies on the allocation reference, which
    `hid_destroy_device()` owns; `hid_bpf_destroy_device()` and
    `hid_remove_device()` are then skipped, or the memory is already freed.
  - Safe: for a reference the transport took with `get_device()` after
    `hid_add_device()` succeeded, as `hidp_session_dev_add()` takes.
