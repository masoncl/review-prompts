- `serdev_device_write_buf()`: exported function in
  `drivers/tty/serdev/core.c`, not a wrapper; one call to
  `ctrl->ops->write_buf`, no `write_lock`, no wait, no need for
  `write_wakeup`.
- `serdev_device_write()`: returns `-EINVAL` whenever
  `serdev->ops->write_wakeup` is NULL, for any timeout.
- `serdev_device_write()` return: `-ETIMEDOUT` or `-ERESTARTSYS` only when
  nothing was written, else the short count; a negative `write_buf` return is
  passed back even after earlier chunks were accepted.
- `serdev_device_write()` with a `write_wakeup` that never calls
  `serdev_device_write_wakeup()`: a partial write waits until the timeout or
  a signal; a timeout of 0 becomes `MAX_SCHEDULE_TIMEOUT`.
- There is no serdev_device_write_room() in this tree.
- `receive_buf`: may sleep; it runs in `flush_to_ldisc()` work with the
  `buf->lock` mutex held, so `serdev_device_write()` is allowed there.
- Callbacks can run before `serdev_device_open()` returns: `ttyport_open()`
  sets `SERPORT_ACTIVE`, then `serdev_device_open()` still calls
  `pm_runtime_get_sync()`.
- `serdev->ops`: dereferenced with no NULL test in
  `serdev_controller_receive_buf()`, `serdev_controller_write_wakeup()` and
  `serdev_device_write()`; only the two members are NULL-tested.
- **Unsafe usage**: `serdev_device_open()` before
  `serdev_device_set_client_ops()`.
  - Unsafe: `serdev_controller_receive_buf()` in `include/linux/serdev.h`
    dereferences `serdev->ops`, which is still NULL.
  - Safe: set the ops, then open, as `hci_uart_register_device_priv()` in
    `drivers/bluetooth/hci_serdev.c` does.
- **Potentially unsafe usage**: `serdev_device_open()` before
  `serdev_device_set_drvdata()`.
  - Unsafe: when `receive_buf` or `write_wakeup` dereferences the driver data
    with no NULL test; `ttyport_open()` sets `SERPORT_ACTIVE`, and
    `ttyport_receive_buf()` calls the client from then on.
  - Safe: when the callback returns on NULL driver data, as
    `scd30_serdev_receive_buf()` in `drivers/iio/chemical/scd30_serial.c`
    does.
  - Safe: set the driver data, then open, as `w1_uart_probe()` in
    `drivers/w1/masters/w1-uart.c` does.
- **Unsafe usage**: calling `serdev_device_write_buf()` or
  `serdev_device_write()` from `write_wakeup`.
  - Unsafe: on a serial core port `uart_write()` takes the port lock, which
    the caller of `uart_write_wakeup()` already holds, for example under
    `serial8250_handle_irq()`.
  - Safe: schedule work from `write_wakeup` and write from the work item, as
    `snd_serial_generic_write_wakeup()` and `snd_serial_generic_tx_work()` in
    `sound/drivers/serial-generic.c` do.
  - Safe: call only `serdev_device_write_wakeup()`, which is one
    `complete()`.
- **Unsafe usage**: calling `serdev_device_close()` from `receive_buf`.
  - Unsafe: `uart_close()` reaches `tty_buffer_flush()` through
    `tty_port_close_start()`, and that takes the `buf->lock` mutex which
    `flush_to_ldisc()` holds while it runs `receive_buf`; after it,
    `release_tty()` calls `tty_buffer_cancel_work()`, which is
    `cancel_work_sync()` on that same work.
  - Safe: close from `remove()` or another task, as
    `hci_uart_unregister_device()` does; `receive_buf` is not running once
    `serdev_device_close()` has returned.
- **Unsafe usage**: calling a termios, tiocm, break, flush or
  wait-until-sent function before a successful `serdev_device_open()` or
  after `serdev_device_close()`.
  - Unsafe: those ops in `drivers/tty/serdev/serdev-ttyport.c` dereference
    `serport->tty`, which is NULL before the first open and is left pointing
    at the released tty by `ttyport_close()` and by a failed
    `ttyport_open()`.
  - Safe: open, then configure, as `gnss_serial_open()` in
    `drivers/gnss/serial.c` does.
- `ttyport_write_buf()` is the only controller op that tests
  `SERPORT_ACTIVE`: on a closed device it returns 0, so
  `serdev_device_write_buf()` reports 0 bytes and `serdev_device_write()`
  waits for its timeout.
