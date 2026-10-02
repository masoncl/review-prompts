- `release_one_tty()`: puts no port and frees no termios. It calls `cleanup`,
  puts the driver and the module, drops the pids and frees the tty.
- The tty core takes no reference on `tty->port`; only drivers call
  `tty_port_get()` and `tty_port_put()`, for example `pty_cleanup()`.
- `struct tty_struct` kref: an open raises `tty->count`, not the kref. The
  initial reference from `alloc_tty_struct()` is dropped by `release_tty()`
  at the final close.
- Other tty references, for example: `port->tty`, `signal->tty` of session
  members, and `tty_lock()` for as long as the lock is held.
- `release_tty()`: runs at the final close under `tty_mutex`, before the last
  kref goes; it calls `shutdown`, saves termios, clears `itty` and cancels
  the buffer work. `cleanup` runs later, in `release_one_tty()`.
- `tty_port_destructor()`: if `port->itty` is still set it warns and returns
  without freeing, so the port leaks. A final `tty_port_put()` from `cleanup`
  is after `release_tty()` cleared `itty`.
- Last `tty_port_put()`: may sleep, since `tty_port_destroy()` cancels the
  buffer work synchronously.
- Last `tty_driver_kref_put()`: may sleep when `TTY_DRIVER_INSTALLED` is set,
  since `destruct_tty_driver()` then removes the proc entry and, without
  `TTY_DRIVER_DYNAMIC_DEV`, the line devices.
- `destruct` in `struct tty_port_operations`: usb-serial does not set one, it
  calls `tty_port_destroy()` itself; `acm_port_destruct()` in
  `drivers/usb/class/cdc-acm.c` is an example of one.
- `driver->flip_wq`: destroyed by `tty_unregister_driver()`, not by
  `destruct_tty_driver()`; a port keeps its pointer in `buf.flip_wq` until
  `tty_port_unregister_device()` or `tty_port_destroy()` clears it.
  `tty_unregister_device()` does not clear it.
