- `hid_bpf_reconnect()` in `drivers/hid/bpf/hid_bpf_dispatch.c`: calls
  `device_reprobe()` directly, inside `hid_bpf_reg()` and `hid_bpf_unreg()`;
  there is no work item.
- `hid_bpf_reconnect()` when the reprobe bit is already set: returns 0 and
  does not reprobe; `hid_device_probe()` clears the bit.
- Reprobe bit: every user passes `ffs(HID_STAT_REPROBED)` to
  `test_and_set_bit()` or `clear_bit()`, so
  `hdev->status & HID_STAT_REPROBED` tests a different bit.
- Return value of `hid_bpf_reconnect()`: ignored by `hid_bpf_reg()` and
  `hid_bpf_unreg()`; the attach succeeds even when the reprobe fails.
- `hdev->bpf_rsize = 0` in `hid_bpf_reconnect()` is what makes the fixup run
  again: `__hid_device_probe()` in `drivers/hid/hid-core.c` calls
  `call_hid_bpf_rdesc_fixup()` only when `bpf_rsize` is 0.
- A reprobe that does not zero `bpf_rsize`, for example from
  `__hid_bus_reprobe_drivers()`, reuses the cached `hdev->bpf_rdesc`.
- Changed descriptor: `__hid_device_probe()` zeroes `hdev->group` and calls
  `hid_set_group()` before `hid_check_device_match()`, so the driver match
  is redone on the new descriptor.
- `hdev->bpf.device_data`: freed by `hid_bpf_disconnect_device()`, called
  from `hid_disconnect()`, so also during a reprobe;
  `hid_bpf_destroy_device()` does not free it.
- `hid_bpf_connect_device()`, from `hid_connect()`: allocates `device_data`
  again when an ops on `prog_list` has `hid_device_event`.
- `struct hid_bpf`: embedded in `struct hid_device` as `bpf`, under
  `CONFIG_HID_BPF`; not freed on its own.
- `__hid_bpf_ops_destroy_device()`: leaves every ops on `prog_list`; it sets
  `hdev` to NULL in each, then drops one device reference per ops after
  releasing `prog_list_lock`.
- `hdev->bpf.destroyed`: read only by `dispatch_hid_bpf_device_event()`,
  `dispatch_hid_bpf_raw_requests()` and `dispatch_hid_bpf_output_report()`,
  which fail with `-ENODEV`; `call_hid_bpf_rdesc_fixup()` does not read it.
- Attach after destroy: fails only because `hid_get_device()` no longer finds
  the device once `hid_remove_device()` has called `device_del()`.
- `hid_destroy_device()`: calls `hid_bpf_destroy_device()` before
  `hid_remove_device()`, so the driver is still bound when `destroyed` is
  set.
- Under `CONFIG_HID_BPF`, from that point `hid_hw_raw_request()` and
  `hid_hw_output_report()` fail with `-ENODEV`, with or without attached
  programs; this covers the driver's `remove` run by `device_del()`.
- Input reports from that point: `-EBUSY` from `__hid_input_report()` while
  `driver_input_lock` is held, otherwise `-ENODEV`.
