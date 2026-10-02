- `command_abort_matching()` with `srb_match` set and `us->srb != srb_match`:
  returns `FAILED`. With `us->srb == NULL`: returns `SUCCESS`.
- `US_FLIDX_TIMED_OUT`: always set once a command matches.
- `US_FLIDX_ABORTING`: set by `command_abort_matching()`, not tested by it.
  It is set, and `usb_stor_stop_transport()` called, only when
  `US_FLIDX_RESETTING` is clear, so an abort cannot cancel the URBs of a
  reset in progress.
- Wait: `wait_for_completion(&us->notify)`, uninterruptible, no timeout. Not
  `us->cmnd_ready`, not `us->dev_mutex`.
- `device_reset()`: calls `command_abort_matching(us, NULL)` first and
  discards its return value, then `us->transport_reset()` under
  `us->dev_mutex`. It does not call `usb_stor_report_device_reset()`.
- `bus_reset()`: calls only `usb_stor_port_reset()`; aborts nothing and takes
  no `us->dev_mutex` itself. `usb_stor_report_bus_reset()` is called from
  `usb_stor_post_reset()` in `drivers/usb/storage/usb.c`.
