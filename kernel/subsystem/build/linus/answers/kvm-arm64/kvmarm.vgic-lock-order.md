- Order in the comment, outermost first: `kvm->lock`, `vcpu->mutex`,
  `kvm->arch.config_lock`, `its->cmd_lock`, `its->its_lock`,
  `vgic_dist->lpi_xa.xa_lock`, `vgic_cpu->ap_list_lock`,
  `vgic_irq->irq_lock`.
- IRQs off: required for the last three locks; `kvm_vgic_early_init()` sets up
  `lpi_xa` with `XA_FLAGS_LOCK_IRQ`.
- **Potentially unsafe usage**: taking `ap_list_lock` or `irq_lock` with plain
  `raw_spin_lock()`.
  - Unsafe: with interrupts enabled; `kvm_arch_timer_handler()` reaches both
    locks through `kvm_vgic_inject_irq()` on the same CPU.
  - Safe: where interrupts are already off, as in `vgic_prune_ap_list()`:
    `kvm_arch_vcpu_ioctl_run()` calls `kvm_vgic_sync_hwstate()` before
    `local_irq_enable()`, and `kvm_vgic_process_async_update()` wraps the
    call in `local_irq_save()`.
  - Safe: nested inside an outer `raw_spin_lock_irqsave()`, as
    `vgic_queue_irq_unlock()` takes `irq_lock` inside `ap_list_lock`.
- `DEBUG_SPINLOCK_BUG_ON()`: empty without `CONFIG_DEBUG_SPINLOCK`.
- Second vCPU's `ap_list_lock`: taken with `raw_spin_lock_nested()` and
  `SINGLE_DEPTH_NESTING`; see `vgic_prune_ap_list()`.
