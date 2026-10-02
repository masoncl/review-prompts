- Callers in `drivers/tty/serial/serial_core.c`, where the context is not
  simply "port lock" or "port mutex":

| Callback | Held by the caller |
|---|---|
| `throttle`, `unthrottle` | nothing; only a port reference |
| `send_xchar` | nothing; only a port reference |
| `tx_empty` | never the port lock; port mutex in `uart_get_lsr_info()` and `uart_suspend_port()`, nothing in `uart_wait_until_sent()` |
| `type` | port mutex, in `uart_line_info()` and `uart_report_port()` |
| `set_termios` | port mutex, never the port lock; `uart_set_options()` takes neither |
| `release_port` | port mutex; in `serial_core_remove_one_port()` only the file-local `port_mutex` |
| `config_port` | port mutex; `uart_configure_port()` adds `console_lock()` when `uart_console()` |

- "Port mutex" is `mutex` in `struct tty_port`; `uart_port_check()` asserts it.
- `tx_empty`, `break_ctl`, `set_termios`: a driver that needs the port lock
  takes it inside, as `serial8250_tx_empty()` does.
- `struct uart_ops` has no `set_wake` member.
- Callbacks reached under the port lock cannot sleep; for the rest, callers in
  `drivers/tty/serial/serial_core.c` hold no spinlock.
- Kernel-doc in `include/linux/serial_core.h` against those callers:

| Callback | Kernel-doc says | Callers do |
|---|---|---|
| `startup` | "port_sem taken", "Interrupts: globally disabled" | port mutex, interrupts on |
| `shutdown` | "port_sem taken" | port mutex |
| `pm`, `type`, `ioctl`, `verify_port`, `request_port`, `config_port` | "Locking: none" | port mutex |
| `release_port` | "Locking: none" | port mutex, except at port removal |
| `tx_empty` | "Locking: none", "must not sleep" | port mutex in two of three callers |
| `set_termios` | "caller holds tty_port->mutex", "must not sleep" | `uart_set_options()` does not take it |

- port_sem is defined nowhere in this tree.
