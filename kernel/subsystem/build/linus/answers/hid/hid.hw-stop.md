- `hid_hw_stop()`: defined in `drivers/hid/hid-core.c`, not an inline.
- Input lock: if `hdev->io_started` is set, `hid_hw_stop()` first calls
  `hid_device_io_stop()`, which clears `io_started` and does `down()` on
  `driver_input_lock`; otherwise it leaves the lock alone.
- Order: `hid_device_io_stop()` (conditional), `hid_disconnect()`,
  `hdev->ll_driver->stop()`.
- `hid_disconnect()` order: removes the `country` attribute first, then
  input, hiddev, hidraw according to `HID_CLAIMED_INPUT`,
  `HID_CLAIMED_HIDDEV`, `HID_CLAIMED_HIDRAW` in `hdev->claimed`, clears
  `claimed`, and calls `hid_bpf_disconnect_device()` last.
- `hid_disconnect()`: does no debug teardown.
- No started state: `hid_hw_stop()` has no test of whether `hid_hw_start()`
  succeeded; it calls `ll_driver->stop()` unconditionally.
- **Unsafe usage**: calling `hid_hw_stop()` after `hid_hw_start()` returned
  an error.
  - Unsafe: `hid_hw_start()` has already run `ll_driver->stop()` when
    `hid_connect()` failed, and a failed `usbhid_start()` has freed its
    buffers; `usbhid_stop()` then calls `hid_free_buffers()` in
    `drivers/hid/usbhid/hid-core.c`, which frees through pointers it never
    clears.
  - Safe: the `hid_hw_start()` failure branch returns without the stop, and
    only later failures reach it, as `ps_probe()` in
    `drivers/hid/hid-playstation.c` does.
