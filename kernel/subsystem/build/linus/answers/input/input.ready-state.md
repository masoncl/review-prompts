- `dev->ready` in `struct input_dev` (`include/linux/input.h`) is the gate:
  `input_event_dispose()` calls `dev->event()` only when the disposition has
  `INPUT_PASS_TO_DEVICE`, `dev->event` is set and `dev->ready` is true.
- `dev->ready` is not `input_device_enabled()`; it is a stored flag, true only
  between a successful `open()` and the matching `close()`.
- `event()` is therefore never called before the first `open()`, after the
  last `close()`, after a failed `open()`, or while inhibited.
- Gate opens in `input_start_device()` and `input_uninhibit_device()`:
  `open()` returns 0, then `ready = true`, then `input_dev_toggle(dev, true)`.
- Gate shuts in `input_close_device()` and `input_inhibit_device()`:
  `input_dev_toggle(dev, false)`, then `ready = false`, then `close()`.
- Device with no `open()` callback: `ready` is still set on the first user.
- `input_uninhibit_device()` with `dev->users == 0`: `ready` stays false and
  nothing is pushed.
- `input_dev_toggle()` calls only `dev->event()`; it does not release keys and
  does not touch the poller.
- `input_dev_toggle(dev, true)`: sends `REP_PERIOD` and `REP_DELAY` whenever
  `EV_REP` is in `dev->evbit`, whatever the values.
- `input_dev_toggle()` itself returns when `!dev->ready`, so
  `input_dev_suspend()`, `input_dev_resume()`, `input_dev_poweroff()` and
  `input_reset_device()` push nothing to a closed or inhibited device.
- Output event while not ready and not inhibited: `input_get_disposition()`
  still records it in `dev->led`, `dev->snd` or `dev->rep` and handlers still
  see it; only the driver call is skipped.
- Replay at gate open covers LED, SND and REP only; `EV_FF`, `EV_MSC`,
  `EV_PWR` and `SYN_CONFIG` sent while not ready are lost to the driver.
