- Documented order, outermost first: `kvm->lock`, `vcpu->mutex`,
  `kvm->arch.config_lock`, `its->cmd_lock`, `its->its_lock`,
  `lpi_xa.xa_lock`, `ap_list_lock`, `irq_lock`.
- `config_lock` has a second documented chain: `kvm->slots_lock`, then
  `kvm->srcu`, then `config_lock`.
- "IRQs disabled" does not mean every acquisition is an `_irqsave` call:
  `vgic_prune_ap_list()` takes `ap_list_lock` with plain `raw_spin_lock()` and
  `vgic_flush_state()` with `scoped_guard(raw_spinlock)`; both rely on the
  caller having IRQs off.
- That reliance is checked by `DEBUG_SPINLOCK_BUG_ON(!irqs_disabled())` in
  `vgic_prune_ap_list()` and `kvm_vgic_flush_hwstate()`, which is empty
  without `CONFIG_DEBUG_SPINLOCK`.
- `irq_lock` nested inside an `ap_list_lock` taken with IRQs off is likewise
  taken with plain `raw_spin_lock()`, for example in
  `vgic_queue_irq_unlock()`.
- `lpi_xa`: initialised with `XA_FLAGS_LOCK_IRQ` in `kvm_vgic_early_init()`.
- Reason given by the comment: `ap_list_lock` may be taken from the timer
  interrupt handler, so it and every lock below it need IRQs off; injection
  from ISRs is the second reason given.
- Two `ap_list_lock`s are taken only in `vgic_prune_ap_list()`;
  `vgic_queue_irq_unlock()` takes one.
