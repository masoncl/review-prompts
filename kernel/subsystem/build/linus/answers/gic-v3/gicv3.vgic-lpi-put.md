- `vgic_put_irq()` uses `refcount_dec_and_lock_irqsave()` on
  `lpi_xa.xa_lock`: the lock is taken only for the drop from one to zero, and
  the final decrement happens under it.
- `vgic_put_irq()` does not call `__vgic_put_irq()`; only
  `vgic_put_irq_norelease()` does.
- `vgic_release_lpi_locked()`: does both `__xa_erase()` and `kfree_rcu()` while
  the xarray lock is still held.
- A lookup under the xarray lock never sees a zero-count object left by
  `vgic_put_irq()`. A lookup under RCU can still load the pointer, and
  `vgic_put_irq_norelease()` does leave zero-count objects in `lpi_xa`.
- Lock debugging: the test is `IS_ENABLED(CONFIG_LOCKDEP)` and the ID being an
  LPI; it really takes and releases `lpi_xa.xa_lock` through
  `guard(spinlock_irqsave)`, before the decrement. It does not call
  `might_lock()`.
