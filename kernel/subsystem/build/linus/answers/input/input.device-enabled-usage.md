- Inside `open()`: `input_device_enabled()` is true, on first open and on
  uninhibit.
- Inside `close()`: false on the last close (`dev->users` is already 0), true
  on inhibit (`dev->inhibited` is set only after `close()` returns).
- `dev->mutex` is the outer lock: the core calls `open()` and `close()` with
  it held, so a suspend or resume callback must take it before any driver
  lock that `open()` or `close()` takes.
- Driver stop in suspend changes none of `dev->users`, `dev->inhibited` or
  `dev->ready`; the core still treats the device as open and may call
  `event()`.
- `lockdep_assert_held()` in `input_device_enabled()`: the only check; without
  lockdep an unlocked call races silently.
- **Unsafe usage**: calling `input_device_enabled()` on a path where nothing
  holds `dev->mutex`.
  - Safe: the callback takes `input->mutex` itself and keeps it across the
    hardware action, as `gpio_keys_suspend()` does; `input_device_enabled()`
    asserts the lock.
  - Safe: a helper that does not lock, when every caller already holds the
    mutex, as `samsung_keypad_toggle_wakeup()` called from
    `samsung_keypad_suspend()` and `samsung_keypad_resume()`.
