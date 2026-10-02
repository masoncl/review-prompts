- `struct irq_ops` has no `flags` field; software resampling is reported by
  the `get_flags()` callback returning `VGIC_IRQ_SW_RESAMPLE`.
- `vgic_irq_needs_resampling()`: defined in `include/kvm/arm_vgic.h`; false
  when `irq->ops` or `irq->ops->get_flags` is NULL.
- The timer's `arch_timer_irq_ops` is `const`;
  `kvm_arch_timer_get_irq_flags()` reads
  `kvm_vgic_global_state.no_hw_deactivation` on every call.
- `get_input_level()`: independent of resampling; an ops may have it and
  still return 0 from `get_flags()`.
- Other callbacks in `struct irq_ops`: `queue_irq_unlock` (replaces the body
  of `vgic_queue_irq_unlock()`) and `set_direct_injection`.
- Installers of `irq->ops`:
  - `kvm_timer_enable()`, for every timer of the vcpu, emulated ones too, and
    before its `kvm_vgic_map_phys_irq()` calls.
  - `vgic_v5_set_ppi_ops()`, from `vgic_v5_setup_private_irq()`, for every
    private interrupt of a GICv5 VM; the timer later replaces it on its own
    interrupts with `arch_timer_irq_ops_vgic_v5`.
- `kvm_vgic_clear_irq_ops()`: installs NULL through
  `kvm_vgic_set_irq_ops()`; nothing in this tree calls it.
- Map and unmap never write `irq->ops`, but both read it for
  `set_direct_injection`; an ops installed after the map misses the
  enable call.
- `irq->ops` set does not imply `irq->hw`: users test `irq->hw` separately,
  for example `vgic_v3_compute_lr()`.
