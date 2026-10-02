- `tty_buffer_queue_work()` in `drivers/tty/tty_buffer.c`: queues `buf->work`
  on `port->buf.flip_wq`, and on `system_dfl_wq` when that pointer is NULL.
- A NULL `port->buf.flip_wq` is a valid state: nothing crashes and the data is
  still delivered.
- `system_unbound_wq` is not used in `drivers/tty/tty_buffer.c`.
- `tty_register_driver()` in `drivers/tty/tty_io.c`: allocates
  `driver->flip_wq` with `alloc_workqueue()`, flags `WQ_UNBOUND | WQ_SYSFS`,
  named from `driver->name` and `driver->driver_name`; it is not `WQ_HIGHPRI`.
- The allocation is the default: it is skipped only when
  `TTY_DRIVER_NO_WORKQUEUE` is set or `driver->driver_name` is NULL.
- `driver->flip_wq` is destroyed by `tty_unregister_driver()` and by the error
  path of `tty_register_driver()`.
- `tty_port_link_driver_wq()` in `include/linux/tty_port.h`: copies
  `driver->flip_wq` into the port only if `port->buf.flip_wq` is NULL.
- `tty_port_link_driver_wq()` is called by `tty_port_register_device_attr()`,
  `tty_port_register_device_attr_serdev()`, `tty_port_install()`, and by
  `tty_register_driver()` for each port already in `driver->ports[]`.
- `tty_port_link_device()`: only sets `driver->ports[index]`; it links no
  workqueue itself.
- `tty_port_link_wq()` in `drivers/tty/tty_port.c`: stores the pointer
  unconditionally and does not test `TTY_DRIVER_NO_WORKQUEUE`; the flag only
  stops the per-driver allocation.
- A workqueue that a driver itself passes to `tty_port_link_wq()` is never
  destroyed by the tty core, which destroys only `driver->flip_wq`; destroying
  it is left to the driver.
- No driver in this tree calls `tty_port_link_wq()` directly; the pty drivers
  set `TTY_DRIVER_NO_WORKQUEUE` and so run on `system_dfl_wq`.
- `tty_port_unregister_device()` and `tty_port_destroy()`: set
  `port->buf.flip_wq` to NULL, a driver-chosen workqueue included, so it has to
  be linked again before the port is reused.
- **Unsafe usage**: `TTY_DRIVER_DYNAMIC_ALLOC` with a `driver_name` and without
  `TTY_DRIVER_NO_WORKQUEUE`.
  - Unsafe: `__tty_alloc_driver()` leaves `driver->ports` NULL, and
    `tty_register_driver()` reads `driver->ports[i]` after it allocates the
    workqueue.
  - Safe: set both flags, as `legacy_pty_init()` and `unix98_pty_init()` in
    `drivers/tty/pty.c` do.
