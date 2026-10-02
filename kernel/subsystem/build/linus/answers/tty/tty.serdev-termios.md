- `ttyport_open()` `c_cflag`: clears `CSIZE` and `PARENB`; sets `CS8`,
  `CRTSCTS` and `CLOCAL`; does not touch `CREAD`, `PARODD`, `CMSPAR` or
  `CSTOPB`.
- `CRTSCTS` is requested on every open; a client without RTS/CTS wiring calls
  `serdev_device_set_flow_control()` with `false`, as `gnss_serial_open()` in
  `drivers/gnss/serial.c` does.
- Starting termios: `tty_init_termios()` takes `driver->termios[idx]` if
  `release_tty()` saved one with `tty_save_termios()`, else `init_termios`.
- Serial core's tty driver does not set `TTY_DRIVER_RESET_TERMIOS`, so speed
  and the untouched bits survive `serdev_device_close()` into the next open.
- `ttyport_open()` calls `tty_init_dev()`, `tty->ops->open()` with a NULL
  file, `tty_unlock()` and `tty_set_termios()`; it ignores the
  `tty_set_termios()` return value.
- Setters in `drivers/tty/serdev/serdev-ttyport.c`: each copies
  `tty->termios` with no lock held, edits the copy, then calls
  `tty_set_termios()`, which takes `termios_rwsem` itself; two concurrent
  setters can lose one change.
- `ttyport_set_parity()`: clears `CMSPAR` as well as `PARENB` and `PARODD`
  before applying the request.
