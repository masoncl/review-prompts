- `struct irq_ops` members: `get_flags`, `get_input_level`,
  `queue_irq_unlock`, `set_direct_injection`.
- `vgic_v5_ppi_irq_ops`: sets `queue_irq_unlock` and `set_direct_injection`;
  `vgic_v5_setup_private_irq()` installs it on all 64 PPIs of every vCPU.
- `arch_timer_irq_ops_vgic_v5`: `kvm_timer_enable()` installs it on the PPIs
  of the vCPU's `nr_timers()` timers; it repeats both GICv5 ops and adds
  `get_input_level`.
- `get_flags`: set by neither GICv5 structure, so
  `vgic_irq_needs_resampling()` is false.
- SPIs and LPIs: have no `struct vgic_irq` for a GICv5 guest, so no ops.
- `vgic_v5_ppi_queue_irq_unlock()`: records nothing; the caller has already
  set `line_level` or `pending_latch`.
- `vgic_v5_ppi_queue_irq_unlock()`: makes `KVM_REQ_IRQ_PENDING` and kicks
  `irq->target_vcpu` without testing enabled or pending, and returns `true`.
- **Unsafe usage**: installing on a GICv5 PPI a `struct irq_ops` that lacks
  the two GICv5 ops; `kvm_vgic_set_irq_ops()` replaces the whole pointer.
  - Unsafe: without `queue_irq_unlock`, `vgic_queue_irq_unlock()` asks
    `vgic_target_oracle()`, which returns `NULL` for a pending PPI because
    `vgic.enabled` is never set for GICv5, so the vCPU is not kicked; an
    active PPI is put on `ap_list`, which `kvm_vgic_sync_hwstate()` never
    prunes for GICv5.
  - Unsafe: without `set_direct_injection`, mapping does not set the bit in
    `vgic_ppi_dvir`, while `kvm_timer_update_irq()` still skips the
    injection.
  - Safe: a structure that repeats both, as `arch_timer_irq_ops_vgic_v5`
    does.
