- Context test in `i2c_in_atomic_xfer_mode()`: `!preemptible()` only with
  `CONFIG_PREEMPT_COUNT`; without it the test is `irqs_disabled()` alone, so a
  context with preemption disabled and interrupts on is not atomic mode.
- `SYSTEM_SUSPEND` is above `SYSTEM_RUNNING`: the interrupts-off part of
  suspend and hibernation is atomic mode too, not only halt, power-off and
  restart; see `suspend_enter()` in `kernel/power/suspend.c`.
- Adapter with no atomic callback: `__i2c_lock_bus_helper()` issues a `WARN()`
  and continues; `__i2c_transfer()` then calls the sleeping `master_xfer`. The
  missing atomic callback does not give `-EOPNOTSUPP`; `__i2c_transfer()`
  returns that when `master_xfer` is NULL.
- The `WARN()` fires only when both `master_xfer_atomic` and
  `smbus_xfer_atomic` are NULL: an adapter with only `smbus_xfer_atomic` gets
  no warning from `i2c_transfer()` in atomic mode and still runs
  `master_xfer`.
- `__i2c_transfer()` and `__i2c_smbus_xfer()` called directly: they pick the
  atomic callback, but the `WARN()` and the trylock are only in
  `__i2c_lock_bus_helper()`, so such callers get neither.
