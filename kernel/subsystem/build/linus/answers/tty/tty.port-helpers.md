- `tty_port_open()`: sets `TTY_PORT_INITIALIZED` after `activate`, not
  `TTY_PORT_ACTIVE`. `TTY_PORT_ACTIVE` is set in
  `tty_port_block_til_ready()`.
- `activate` is optional: with none, `tty_port_open()` still sets
  initialized.
- `activate` returning nonzero, positive too: `tty_port_open()` returns the
  value at once, leaves initialized clear and skips
  `tty_port_block_til_ready()`. `uart_open()` maps a positive value to 0.
- `tty_port_close()`: does nothing more when `tty_port_close_start()` returns
  0, which is every close but the last, and every close of a hung-up file.
- `tty_port_shutdown()` on a port with `port->console` set: returns before it
  tests or clears initialized, so `tty_port_close()` and `tty_port_hangup()`
  never call `shutdown` and leave initialized set; the next
  `tty_port_open()` then skips `activate`.
- `tty_port_close()` does not set `TTY_IO_ERROR` on a console port.
- `tty_port_hangup()`: also sets `TTY_IO_ERROR` on the tty, under
  `port->lock`.
- `TTY_PORT_ACTIVE`: the helpers in `drivers/tty/tty_port.c` only write it.
  `uart_hangup()` is the only reader in this tree.
- `tty_port_block_til_ready()` returns 0 without waiting in two cases:
  - `tty_io_error()` is true: it sets active and does not touch DTR/RTS.
  - the file is NULL or has `O_NONBLOCK`: it raises DTR/RTS only if `C_BAUD`
    is nonzero, then sets active.
