- First `event()` call: `input_dev_toggle(dev, true)` in
  `input_start_device()`, straight after `open()`, under `event_lock` with
  interrupts off; it sends the state of every LED in `ledbit`, every sound in
  `sndbit` and, with `EV_REP`, both repeat values.
- `getkeycode()` and `setkeycode()`: not gated by `dev->ready`;
  `input_get_keycode()` and `input_set_keycode()` call them under
  `event_lock`, from evdev ioctls and from `drivers/tty/vt/keyboard.c`.
- During `input_register_device()`, `open()` called from a handler's connect
  runs in the registering thread, with `input_mutex` and `dev->mutex` held.
