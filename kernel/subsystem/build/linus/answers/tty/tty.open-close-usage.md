- `tty_open()`: when `open` fails or is NULL, it drops `tty_lock()` and calls
  `tty_release()`, which calls `close` with the same file.
- `ptmx_open()` does the same through `tty_release()`; `ttyport_open()` calls
  `close` directly, with a NULL file.
- If that was the only open, `tty_release()` goes on to `release_tty()`, so
  `shutdown` and later `cleanup` of `struct tty_operations` run too.
- `tty_port_close_start()`: drops `port->count` for any file that is not hung
  up. The initialized bit gates only the drain there, and `shutdown` in
  `tty_port_shutdown()`.
- After a failed `activate`: the port `shutdown` is not called, since
  initialized was never set; `port->tty` stays set until `tty_port_close()`
  clears it.
- A blocking open that fails because of a hangup:
  `tty_port_block_til_ready()` does not restore `port->count`, and
  `tty_port_close_start()` skips the hung-up file, so the count stays
  balanced.
- `uart_install()` sets `tty->driver_data` before `open` can run, so
  `uart_close()` can find its state after any failure in `uart_open()`.
