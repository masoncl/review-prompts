- Guard: `uart_port_lock_check_sysrq_irqsave`; it unlocks with
  `uart_unlock_and_check_sysrq_irqrestore()`. See `serial8250_handle_irq()`.
- No guard exists for `uart_unlock_and_check_sysrq()`, and no conditional
  variant.
- `serial8250_handle_irq_locked()`: its caller must release the lock with that
  guard or with `uart_unlock_and_check_sysrq_irqrestore()`.
- `uart_handle_sysrq_char()`: defined here and used by many drivers; with
  `CONFIG_MAGIC_SYSRQ_SERIAL` it calls `handle_sysrq()` at once, under the
  port lock; without it, a stub that returns 0.
- `uart_prepare_sysrq_char()`: does not test `has_sysrq`; in
  `include/linux/serial_core.h` only `uart_handle_break()` and the two unlock
  helpers do.
- `has_sysrq` clear: the unlock helpers skip `sysrq_ch` entirely.
- `uart_handle_break()`: a second break disarms `sysrq` whenever it is
  non-zero; there is no time test.
- **Unsafe usage**: `uart_prepare_sysrq_char()` followed by
  `uart_port_unlock()`, an irq variant of it, or a plain port-lock guard.
  - Unsafe: `sysrq_ch` stays set and `handle_sysrq()` does not run until some
    later check_sysrq unlock.
  - Safe: `uart_unlock_and_check_sysrq()` or
    `uart_unlock_and_check_sysrq_irqrestore()` on every exit path.
  - Safe: `guard(uart_port_lock_check_sysrq_irqsave)`, as
    `serial8250_handle_irq()` does.
- **Potentially unsafe usage**: `uart_handle_sysrq_char()` under the port
  lock.
  - Unsafe: when the console `write` of that port takes the port lock while
    `sysrq` is non-zero.
  - Safe: when `write` skips the lock if `sysrq` is set, as
    `s3c24xx_serial_console_write()` does; `uart_handle_sysrq_char()` clears
    `sysrq` only after `handle_sysrq()` returns.
