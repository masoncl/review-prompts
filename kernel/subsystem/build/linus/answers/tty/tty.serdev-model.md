- `tty_port_register_device_attr_serdev()`: the test is
  `PTR_ERR(dev) != -ENODEV` on the `struct device *` from
  `serdev_tty_port_register()`; success and every other error skip the cdev.
- `tty_port_register_device_attr_serdev()` tests no driver flag or type; its
  only caller is `serial_core_add_one_port()` in
  `drivers/tty/serial/serial_core.c`.
- `serial_core_add_one_port()` when `tty_port_register_device_attr_serdev()`
  returns an error: the port has neither cdev nor serdev controller;
  `serdev_tty_port_register()` puts its controller on its error path.
- Controller with no child: `serdev_controller_add()` succeeds, and the cdev
  is suppressed, in two cases where no client was enumerated from firmware:
  - `of_serdev_register_devices()` returns 0 when the controller node has a
    graph (`of_graph_is_present()`).
  - `acpi_serdev_register_devices()` returns 0 when
    `acpi_quirk_skip_serdev_enumeration()` sets `skip`.
- `ctrl->serdev` is NULL in those cases until other code calls
  `serdev_device_alloc()` and `serdev_device_add()`, for example
  `drivers/power/sequencing/pwrseq-pcie-m2.c`.
- `port->client_ops` is not saved: the error path of
  `serdev_tty_port_register()`, and `serdev_tty_port_unregister()`, both
  write `&tty_port_default_client_ops`.
- RX entry: `receive_buf()` in `drivers/tty/tty_buffer.c`, called from
  `flush_to_ldisc()`, calls `port->client_ops->receive_buf`; the tty's line
  discipline is not consulted.
- Line discipline: `tty_init_dev()` still opens one with `tty_ldisc_setup()`,
  and `tty_set_termios()` still calls its `set_termios`; RX and write wakeup
  bypass it.
- `ttyport_receive_buf()`: gated on `SERPORT_ACTIVE`, not on `serdev->ops`;
  the flag bytes `fp` are dropped, so the client sees no break, parity or
  framing marks.
- Short return from the client: `flush_to_ldisc()` offers the remainder again
  at once if the return was non-zero; on 0 it stops, and the bytes wait until
  the work is queued again, which nothing under `drivers/tty/serdev/` does.
- `ttyport_write_wakeup()`: calls the client only if `TTY_DO_WRITE_WAKEUP`
  was set and `SERPORT_ACTIVE` is set; `ttyport_write_buf()` is the only
  serdev code that sets `TTY_DO_WRITE_WAKEUP`.
- `serdev_controller_write_wakeup()` with a NULL `write_wakeup` member:
  returns without calling anything; there is no default, and
  `serdev->write_comp` is not completed.
