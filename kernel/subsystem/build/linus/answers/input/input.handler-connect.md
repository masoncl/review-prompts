- On device removal, `disconnect()` runs after `input_disconnect_device()`,
  which has already set `dev->going_away` and written 0 to `handle->open` on
  every handle of the device.
- `input_close_device()` in `disconnect()` is still needed on that path to
  drop `dev->users`; it leaves `handle->open` at -1.
- **Potentially unsafe usage**: calling `input_open_device()` on a
  `struct input_handle` that an earlier `disconnect()` already closed.
  - Unsafe: when `handle->open` is left at -1; the open brings it to 0, so
    `input_pass_values()` skips the handle and `start()` is not called.
  - Safe: a handle from a zeroing allocation, as in `kbd_connect()` in
    `drivers/tty/vt/keyboard.c`; `input_open_device()` then brings
    `handle->open` from 0 to 1.
  - Safe: an embedded handle whose `handle->open` is reset to 0 first, as in
    `appletb_kbd_inp_connect()` in `drivers/hid/hid-appletb-kbd.c`.
- `handler->id_table`, `handler->connect` and `handler->disconnect`: used with
  no NULL test, in `input_match_device()`, `input_attach_handler()`,
  `__input_unregister_device()` and `input_unregister_handler()`.
