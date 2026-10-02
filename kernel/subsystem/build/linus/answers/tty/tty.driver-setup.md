- `init_termios`: there is no default; `__tty_alloc_driver()` zero-fills the
  driver, so the driver copies `tty_std_termios` itself.
- `write_room` missing while `write` is set: `file_tty_write()` logs
  "missing write_room method" on each write and goes on; `tty_write_room()`
  returns 2048.
- After a failed `tty_register_driver()`: a `driver->flip_wq` that was
  allocated is already destroyed, and ports that were in `driver->ports`
  still point at it until `tty_port_destroy()` clears `buf.flip_wq`;
  `uart_register_driver()` shows the cleanup order.
