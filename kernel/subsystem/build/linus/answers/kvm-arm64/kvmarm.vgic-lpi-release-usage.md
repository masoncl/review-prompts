- `vgic_put_irq()` on an LPI: the final put takes `lpi_xa.xa_lock` through
  `refcount_dec_and_lock_irqsave()`.
- `lpi_xa.xa_lock`: a `spinlock_t` that ranks above both raw locks.
- **Unsafe usage**: calling `vgic_put_irq()` on an interrupt that may be an
  LPI while holding an `ap_list_lock` or an `irq_lock`.
  - Safe: unlock first, then put, as `kvm_vgic_inject_irq()` does after
    `vgic_queue_irq_unlock()` has dropped every lock.
  - Safe: inside `arch/arm64/kvm/vgic/vgic.c`, call
    `vgic_put_irq_norelease()` under the lock, keep its result, and call
    `vgic_release_deleted_lpis()` after the last raw lock is dropped, as
    `vgic_prune_ap_list()` does.
- Holding a second reference: does not make the put acceptable; with
  `CONFIG_LOCKDEP`, `vgic_put_irq()` takes and drops `xa_lock` on every LPI
  put, before the decrement.
- Lockdep annotation: a real acquire through `guard(spinlock_irqsave)`,
  guarded by `IS_ENABLED(CONFIG_LOCKDEP)`; it does not call `might_lock()`.
- `vgic_put_irq()` on a non-LPI: returns before it touches `lpi_xa`.
- `vgic_put_irq_norelease()`: `__must_check`, wraps `__vgic_put_irq()`, returns
  true when the count reached 0.
- Dead LPI: stays in `lpi_xa` with count 0; no field marks it.
- `vgic_release_deleted_lpis()`: walks all of `lpi_xa` and releases every
  entry whose count is 0, not only the caller's.
- `vgic_put_irq_norelease()` and `vgic_release_deleted_lpis()`: `static` in
  `arch/arm64/kvm/vgic/vgic.c`; code in other files has only the unlock-first
  form.
