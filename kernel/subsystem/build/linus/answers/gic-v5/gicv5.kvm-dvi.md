- Path: `kvm_vgic_map_phys_irq()` calls `kvm_vgic_map_irq()`, which sets
  `irq->hw` and then calls `irq->ops->set_direct_injection(vcpu, irq, true)`.
- `set_direct_injection`: member of `struct irq_ops` in
  `include/kvm/arm_vgic.h`. Both `vgic_v5_ppi_irq_ops` and
  `arch_timer_irq_ops_vgic_v5` point it at `vgic_v5_set_ppi_dvi()`.
- Recorded in: per-vCPU `vgic_ppi_dvir` in `struct vgic_v5_cpu_if`, not per
  VM. The per-interrupt mark is `irq->hw`; `struct vgic_irq` has no separate
  direct-injection flag.
- Switched on: every guest entry, first write of
  `__vgic_v5_restore_ppi_state()`. Not at load.
- Switched off: every guest exit, last writes of
  `__vgic_v5_save_ppi_state()`. Not at put.
- Software injection: for a GICv5 guest `kvm_timer_update_irq()` returns
  before `kvm_vgic_inject_irq()` when the timer is `direct_vtimer` or
  `direct_ptimer`, so it does not update the shadow `line_level` of those
  PPIs.
- Unmap: `kvm_vgic_unmap_irq()` passes `irq->target_vcpu` and false. The only
  callers of `kvm_vgic_unmap_phys_irq()` are in
  `kvm_timer_vcpu_load_nested_switch()`, which `kvm_timer_vcpu_load()` does not
  call for a GICv5 guest.
