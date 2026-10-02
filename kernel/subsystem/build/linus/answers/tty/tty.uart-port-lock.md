- Wrappers: call `spin_lock()` or its irq variant on `lock`, then
  `__uart_port_nbcon_acquire()`; unlock calls `__uart_port_nbcon_release()`
  first.
- `__uart_port_lock_irqsave()`: the raw lock with no nbcon step; for
  `device_lock` callbacks and `uart_port_set_cons()` only.
- nbcon_locked_port: no such field in this tree.
- `uart_port_unlock()` and its irq variants: do not look at `sysrq_ch`.
- Guards: `uart_port_lock`, `uart_port_lock_irq`, `uart_port_lock_irqsave`,
  `uart_port_lock_check_sysrq_irqsave`; conditional `_try` variants of
  `uart_port_lock` and `uart_port_lock_irqsave` only, from
  `DEFINE_GUARD_COND()` and `DEFINE_LOCK_GUARD_1_COND()`.
- Initialised in `uart_port_spin_lock_init()`: `spin_lock_init()` plus one
  lockdep class, `port_lock_key`, for every port.
- `serial_core_add_one_port()`: initialises the lock unless
  `uart_console_registered()`.
- `uart_set_options()`: initialises the lock unless
  `uart_console_registered_locked()` or `console_reinit` is set; its caller
  must hold `console_list_lock()`.
- Earlycon: `register_earlycon()` and `of_setup_earlycon()` initialise the
  lock of their own port.
- Drivers also call `spin_lock_init()` themselves, for example
  `serial8250_init_port()`.
- **Unsafe usage**: `spin_lock()` or a variant directly on `lock` of
  `struct uart_port`.
  - Unsafe: on a port that can be an nbcon console; `write_atomic` runs
    without the port lock and is kept out only by nbcon ownership.
  - Safe: `__uart_port_lock_irqsave()` inside `device_lock`, as
    `univ8250_console_device_lock()` does; `nbcon_emit_one()` acquires
    ownership itself afterwards.
  - Safe: any `uart_port_lock()` wrapper or guard.
