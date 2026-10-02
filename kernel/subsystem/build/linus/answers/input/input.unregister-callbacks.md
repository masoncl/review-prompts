- There is no __input_close_device() here; `evdev_disconnect()` calls
  `evdev_cleanup()`, which calls `input_close_device()` when `evdev->open` is
  non-zero. `evdev_mark_dead()` only clears `evdev->exist`.
- `input_dev_toggle(dev, false)` calls `event()` with value 0 for each LED
  and sound that is on, so `event()` runs during unregistration, before
  `close()`.
- `close()` is skipped when `dev->inhibited` is set; `input_inhibit_device()`
  already called it if the device had users.
- During unregistration `close()`, `flush()` and `event()` run in the
  thread that unregisters, with `input_mutex` held.
- `input_event()` afterwards: nothing in the event path tests `going_away`;
  `input_get_disposition()` still updates `dev->key`, `dev->sw` and
  `absinfo` values.
- `input_event()` afterwards does not call `dev->event()`: `dev->ready` is
  clear once the device was closed or inhibited.
- A key press reported and synced afterwards on a device with `EV_REP`,
  `EV_KEY` and softrepeat re-arms `dev->timer` through
  `input_start_autorepeat()`; `input_dev_release()` does not delete that
  timer.
