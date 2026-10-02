- Transmit buffer: `xmit_buf` and `xmit_fifo` live in the `struct tty_port`
  embedded in `struct uart_state`; `struct uart_state` itself has no buffer.
- State array: allocated with `kzalloc_objs()` in `uart_register_driver()`.
- 8250 sub-drivers: do not own the registered `struct uart_port`.
  `serial8250_register_8250_port()` copies selected fields of the caller's
  `struct uart_8250_port` into a slot of the static `serial8250_ports[]` in
  `drivers/tty/serial/8250/8250_core.c` and registers that slot; the caller's
  struct is only a template and is often on the stack.
- `uart_port_ref()`: takes no lock; `atomic_add_unless(&state->refcount, 1, 0)`
  then returns `state->uart_port`.
- `uart_port_check()`: tests nothing; it asserts `state->port.mutex` with
  lockdep and returns `state->uart_port`. It does not look at `UPF_DEAD`.
- Reference plus port lock: `uart_port_ref_lock()` and
  `uart_port_unlock_deref()`, static inlines in
  `drivers/tty/serial/serial_core.c`; `uart_port_unlock_deref()` accepts NULL.
- `uart_port_lock()` and `uart_port_unlock()` in
  `include/linux/serial_core.h`: take a `struct uart_port *` and only the port
  spinlock (and the nbcon ownership for a registered nbcon console); they take
  no reference.
