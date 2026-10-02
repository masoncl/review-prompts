- `__pm_runtime_resume()`: its `might_sleep_if()` has a third condition,
  `dev->power.runtime_status != RPM_ACTIVE`; the other two functions test
  only `RPM_ASYNC` and `power.irq_safe`.
- Synchronous resume of a device that is `RPM_ACTIVE`: passes the check, and
  `rpm_resume()` returns 1 without dropping `power.lock`.
- That status read is made without the lock and before `usage_count` is
  incremented; it holds only if the caller already keeps the device active.
- `__pm_runtime_idle()` and `__pm_runtime_suspend()` with `RPM_GET_PUT`:
  return 0 before the `might_sleep_if()` when the count stays above zero, so
  the check fires only on the call that drops the last count.
- With `irq_safe`: `__rpm_callback()` and `rpm_idle()` do drop `power.lock`
  around the callback, with `spin_unlock()`; only interrupts stay disabled.
- The kerneldoc of `pm_runtime_irq_safe()` says the callbacks run "with the
  spinlock held"; the code does not do that.
- `pm_runtime_irq_safe()`: raises the parent's `usage_count` with
  `pm_runtime_get_sync()`, not `child_count`, and ignores the return value.
- `pm_runtime_irq_safe()`: does not test whether the parent is `irq_safe`
  and prints no warning.
- `pm_runtime_irq_safe()` itself: needs process context with interrupts on;
  it calls `pm_runtime_get_sync()` on the parent and uses `spin_lock_irq()`.
