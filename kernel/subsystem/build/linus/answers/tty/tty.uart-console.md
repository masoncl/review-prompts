- `uart_console()`: under `CONFIG_SERIAL_CORE_CONSOLE`, tests only `cons`
  non-NULL and `cons->index == line`; no `CON_ENABLED` and no registration
  test. Without that option it is constant 0.
- `index` of `struct console`: `drivers/tty/serial/serial_core.c` never writes
  it.
- `cons` of `struct uart_port`: every port of a driver gets the same pointer
  from `serial_core_add_one_port()`; only the `index` compare tells them apart.
- `uart_port_set_cons()`: the only way to write `cons` of `struct uart_port`;
  `__uart_port_using_nbcon()` relies on it changing under the port lock.
- `device_lock`, `device_unlock`: take the port lock with
  `__uart_port_lock_irqsave()` and `__uart_port_unlock_irqrestore()`, not the
  `uart_port_lock_irqsave()` wrapper.
- `nbcon_emit_one()` in `kernel/printk/nbcon.c`, when `use_atomic` is false:
  calls `device_lock`, then acquires nbcon ownership itself, then calls
  `write_thread`.
- `write_atomic`: called with no `device_lock`; nbcon ownership is its only
  serialisation against the driver.
- `register_console()` and `unregister_console_locked()`: hold `device_lock`
  while changing the console list, when `CON_NBCON` and `write_atomic` are set.
- `nbcon_alloc()`: fails with a warning unless `write_thread`, `device_lock`
  and `device_unlock` are all set.
- Driver: `univ8250_console` in `drivers/tty/serial/8250/8250_core.c`, writing
  through `serial8250_console_write()`.
- Other nbcon serial consoles: search `CON_NBCON` under `drivers/tty/serial`;
  for example `pl011_console_write_atomic()`.
