- `hid_disconnect()` and `ll_driver->stop()`: at remove, reached only
  through `hid_hw_stop()`; with a `remove` callback the core runs neither.
- `hid_device_io_stop()` before `hid_hw_stop()` in `remove`: not needed,
  `io_started` is false at entry; calling it only logs "io already stopped".
- `hid_hw_close()`: `hid_hw_stop()` closes only for its listeners
  (`hidraw_disconnect()` calls `hid_hw_close()` for an open node); a
  driver's own `hid_hw_open()` left open keeps `hdev->ll_open_count`
  non-zero for the next driver bound, whose first `hid_hw_open()` then skips
  `ll_driver->open()`.
- State used by listener callbacks (force feedback, LED events): must stay
  valid until `hid_hw_stop()` returns; `raw_event` is not among them, see
  "Core work around remove".
- **Potentially unsafe usage**: a `remove` callback with a path that returns
  before `hid_hw_stop()` has run, in a driver with no devres action that
  runs it.
  - Unsafe: when probe can succeed in the state that takes that path and
    leave the hardware started; `hid_device_remove()` then runs
    `hid_close_report()` with the listeners still registered and the
    transport never stopped.
  - Safe: when probe cannot leave the hardware started in that state, as
    `ft260_remove()` in `drivers/hid/hid-ft260.c` returns for NULL driver
    data: `ft260_probe()` sets the driver data before its final `return 0`,
    and its other return of 0, when `ft260_is_interface_enabled()` returns 0,
    comes after its own `hid_hw_close()` and `hid_hw_stop()`.
  - Safe: stop on every path, including the one where probe returned after a
    bare `hid_hw_start()` with no driver data, as `hidpp_remove()` in
    `drivers/hid/hid-logitech-hidpp.c` does with
    `if (!hidpp) return hid_hw_stop(hdev);`.
  - Safe: driver cleanup, `hid_hw_close()` matching the `hid_hw_open()` of
    probe, then `hid_hw_stop()`, as `ps_remove()` in
    `drivers/hid/hid-playstation.c`.
  - Safe: no stop in `remove` when a devres action does it, as
    `hammer_remove()` in `drivers/hid/hid-google-hammer.c`; see "Stopping
    hardware from devres".
