- There is no uart_change_speed() here; `uart_change_line_settings()` calls
  `set_termios`.
- First open: `uart_port_activate()` passes `init_hw` false, so
  `uart_port_startup()` does not raise DTR/RTS.
- First open, DTR/RTS: raised after `set_termios` by
  `tty_port_block_til_ready()` through `uart_dtr_rts()`, when `C_BAUD()`.
- `init_hw` true: only from `uart_set_info()` and `uart_do_autoconfig()`.
- `serial_base_port_startup()`: last step of `uart_startup()`, after
  `set_termios`; calls no driver callback.
- `set_mctrl` from `uart_update_mctrl()`: skipped when `mctrl` does not change
  or `SER_RS485_ENABLED` is set.
- `pm` from `uart_change_pm()`: skipped when the state does not change;
  `uart_configure_port()` leaves a console port at `UART_PM_STATE_ON`.
- Last close, in order: `tx_empty` polling in `uart_wait_until_sent()`;
  `set_mctrl` dropping DTR/RTS if `HUPCL`; `stop_rx`; `shutdown`; `pm` OFF.
- Last close, DTR/RTS: dropped by `tty_port_shutdown()` before it calls
  `uart_tty_port_shutdown()`.
- `uart_tty_port_shutdown()`: does not call `uart_shutdown()`.
- `uart_hangup()`: does not call `tty_port_hangup()`; it runs
  `uart_flush_buffer()` then `uart_shutdown()` itself, only when
  `tty_port_active()`.
- Hangup of an active, initialised port, in order: `flush_buffer`; `set_mctrl`
  if `HUPCL`; `shutdown`; `pm` OFF. No `stop_rx`.
- Console, last close: `tty_port_shutdown()` returns at its `console` test;
  after the `tx_empty` polling no callback runs and the port stays
  initialised.
- Console, next open after such a close: `tty_port_open()` skips
  `uart_port_activate()`, so no `startup` or `set_termios`.
- Console, hangup: `shutdown` is still called and DTR/RTS still dropped under
  `HUPCL`; only `pm` OFF is skipped.
- Console, hangup: `uart_shutdown()` saves cflag and speeds into
  `struct console`; the next `uart_port_startup()` restores them.
- Console test differs: close uses `console` in `struct tty_port`, written
  once in `serial_core_add_one_port()`; hangup uses `uart_console()` live.
