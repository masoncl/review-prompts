- Probe failure: `__hid_device_probe()` calls `hid_device_io_stop()` when
  `io_started` is still set, before it releases the devres group.
  `hid_device_probe()` then does the `up()`.
- Driver error path: needs no `hid_device_io_stop()` of its own.
  `mcp2221_probe()` returns errors after `hid_device_io_start()` without it.
- `hid_device_io_stop()` with I/O already stopped: `dev_warn()` and no
  `down()`. An explicit stop goes before `hid_hw_stop()`, as in
  `nintendo_hid_probe()`, not after.
- `hdev->io_started` after a probe that returned with I/O started: stays true.
  Only `hid_device_probe()`, `hid_device_remove()` and `hid_device_io_stop()`
  clear it.
- **Unsafe usage**: calling `hid_hw_stop()` outside probe and remove on a
  device whose probe left I/O started. It takes `driver_input_lock` and
  nothing releases it: every report gets `-EBUSY` and `hid_device_remove()`
  blocks in `down()`.
  - Safe: in `remove`, as `logi_dj_remove()` does; `hid_device_remove()` has
    cleared `io_started` and holds the semaphore already.
  - Safe: in the error path of `probe`, as `hidpp_probe()` does; the core
    releases the semaphore after `probe` returns.
