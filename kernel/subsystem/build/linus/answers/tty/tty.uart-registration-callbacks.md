- `uart_configure_port()` early return: only when `uart_iotype_mmio()` or
  `uart_iotype_io()` is true for `port->iotype` and `iobase`, `mapbase` and
  `membase` are all zero. A `UPIO_BUS` port with no base address goes on.
- Gate for everything after `config_port()`: `port->type != PORT_UNKNOWN`.

| Callback | Made when | NULL test |
|---|---|---|
| `ops->config_port()` | `UPF_BOOT_AUTOCONF` set | none |
| `ops->type()` | type known | yes |
| `ops->pm()` | type known; ON, then OFF unless `uart_console()` | yes |
| `ops->set_mctrl()` | type known and `SER_RS485_ENABLED` clear | none |
| `port->rs485_config()` | type known and `SER_RS485_ENABLED` set | none |
| console `setup()` and write | from `register_console()`, called when type known, `port->cons` set and not registered | - |

- `config_port()` flags: `port->type` is reset to `PORT_UNKNOWN` and
  `UART_CONFIG_TYPE` is passed only when `UPF_FIXED_TYPE` is clear.
- `set_mctrl()`: also called for a console port; `port->mctrl` is masked to
  `TIOCM_DTR`, plus `TIOCM_RTS` when `uart_console_hwflow_active()` is true.
- `port->rs485_config()`: called from `uart_rs485_config()` under the port
  lock with a NULL termios.
- `register_console()`: the test is on `port->cons`, which
  `serial_core_add_one_port()` has just set to `drv->cons`; it does not test
  `uart_console(port)`, so adding any line of a driver with a console can
  register that console.
- 8250 sub-drivers: `serial8250_register_8250_port()` ORs in
  `UPF_BOOT_AUTOCONF`, so `config_port()` runs on every registration that
  passes the early return.
- `startup()` and the other open-time callbacks: not made by the registering
  task, except `set_termios()` when the driver's console `setup()` calls
  `uart_set_options()`. An open from another task blocks in `tty_port_open()`
  on `state->port.mutex`, which `serial_core_add_one_port()` holds until it
  returns; the open can then run before the driver executes its next
  statement after `uart_add_one_port()`.
- **Unsafe usage**: setting up, after `uart_add_one_port()`, anything that
  `startup()`, `set_termios()` or `start_tx()` dereference.
  - Safe: set driver data and private pointers before the call, as
    `stm32_usart_serial_probe()` does with `platform_set_drvdata()`;
    `tty_port_open()` is what can call `uart_port_activate()` at once.
