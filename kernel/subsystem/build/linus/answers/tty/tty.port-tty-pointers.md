- `tty_port_install()` sets `tty->port`, not `port->tty`.
- `port->tty` is set by `tty_port_tty_set()`, which `tty_port_open()` calls
  before `activate`. The open path in `drivers/tty/tty_io.c` never sets it.
- A driver that uses neither `tty_port_open()` nor `tty_port_tty_set()` has
  `port->tty` NULL all the time, for example pty; `tty_port_tty_get()` and
  `tty_port_tty_wakeup()` then find no tty.
- `port->tty` is cleared by `tty_port_close()` on the last close and by
  `tty_port_hangup()`, which clears it under `port->lock` and puts the
  reference after the port `shutdown`.
- `scoped_guard(tty_port_tty, port)` with `scoped_tty()`, from
  `include/linux/tty_port.h`: gets the tty, skips the body if it is NULL, and
  puts it at the end; see `__tty_port_tty_hangup()`.
- `port->itty` is set in `tty_init_dev()` after `tty_ldisc_lock()` succeeds,
  and for the pty slave in `pty_common_install()`.
- `port->itty` is cleared in `release_tty()`, for the tty and its link, just
  before `tty_buffer_cancel_work()`.
- `port->itty` readers on the receive path: `tty_port_default_receive_buf()`
  and `tty_port_default_lookahead_buf()`, with `READ_ONCE()` and no
  reference; they run from the buffer work that `release_tty()` cancels.
