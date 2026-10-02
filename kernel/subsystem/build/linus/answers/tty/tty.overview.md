- Default receive path: `tty_port_default_receive_buf()` reads `port->itty`,
  not `port->tty`, so data can still reach the ldisc while `port->tty` is
  NULL.
- `port->itty`: set and cleared with no kref taken or put.
- `release_tty()`: unhooks the tty from the driver as well as from the port;
  `tty_driver_remove_tty()` calls `remove` of `struct tty_operations`, or
  clears the `driver->ttys[]` slot when there is none.
- `struct tty_port` lifetime depends on the driver:

  | Owner | Port memory | Freed by |
  |---|---|---|
  | serial core | `struct uart_state` array of the `struct uart_driver` | `uart_unregister_driver()`; kref unused, `uart_port_ops` has no `destruct` |
  | pty | one per end, both allocated in `pty_common_install()` | `tty_port_put()` in `pty_cleanup()`, so it dies with its tty |

- `TTY_DRIVER_DEVPTS_MEM` and `TTY_DRIVER_DYNAMIC_ALLOC`: Unix98 ptys set
  both, in `unix98_pty_init()`.
- `tty_kopen_exclusive()`: gives a tty with no `struct file`.
- `tty->ldisc`: NULL after a hangup that does not reinit (`tty_ldisc_kill()` in
  `tty_ldisc_hangup()`), until `tty_reopen()` reinstates it. `tty_ldisc_ref()`
  returns NULL then, and also while a writer holds or waits for `ldisc_sem`.
- `xmit_buf` of a serial core port: exists only between
  `uart_alloc_xmit_buf()` and `uart_free_xmit_buf()`; the write paths test it
  for NULL.
- `state->uart_port`: `uart_port_ref()` with `uart_port_deref()` pins it
  through `state->refcount`. `uart_port_check()` asserts `port.mutex` instead.
- `serial_core_remove_one_port()`: waits on `remove_wait` for the refcount to
  drain before it clears `state->uart_port`.
- `struct serial_ctrl_device`, `struct serial_port_device`
  (`drivers/tty/serial/serial_base.h`): devices on the `serial-base` bus that
  `uart_add_one_port()` creates between the hardware device and the tty device.
- Device chain: `uport->dev`, then ctrl, then port (`uport->port_dev`), then
  the tty device. `__uart_start()` does runtime PM on `port_dev`.
- `struct console` and the open path: `/dev/console` resolves in
  `tty_lookup_driver()` through `console_device()` and the console's `device`
  hook. For serial that is `uart_console_device()`, where `co->data` is the
  `struct uart_driver`.
- `uart_port_lock()` and its variants: also take nbcon ownership of
  `uport->cons` when `uart_console()` is true for the port and the console is
  registered, `CON_NBCON`, with `write_atomic`. A bare
  `spin_lock(&uport->lock)` does not.
