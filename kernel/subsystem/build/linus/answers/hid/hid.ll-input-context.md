- `hid->driver` NULL: tested straight after the trylock succeeds, before
  HID-BPF, `raw_event`, hiddev and hidraw; nothing sees the report.
- `-EBUSY`: returned whenever anything holds `hid->driver_input_lock`, not
  only probe or remove; for example another report in flight,
  `hid_debug_rdesc_show()` in `drivers/hid/hid-debug.c`, or
  `hid_bpf_input_report()`.
- `hid_device_io_start()` called in probe: does the `up()`, so reports are
  delivered for the rest of probe and `hid_device_probe()` skips its own
  `up()` (it tests `hdev->io_started`).
