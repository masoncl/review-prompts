- Flag: `resident` in `struct gicv5_vpe`
  (`include/linux/irqchip/arm-gic-v5.h`), the `gicv5_vpe` member of
  `struct vgic_v5_cpu_if`.
- Priorities: copied only by `vgic_v5_put()` when the vCPU flag `IN_WFI` is
  set, and only after the `resident` test has passed. A put outside WFI, or a
  put that returns early, copies nothing.
- `IN_WFI`: set by `kvm_vcpu_wfi()` in `arch/arm64/kvm/arm.c` just before its
  `kvm_vgic_put()`.
- Helper: `vgic_v5_sync_ppi_priorities()`; it writes `irq->priority` under
  `irq_lock` for exposed PPIs only.
- Source: `cpu_if->vgic_ppi_priorityr[]`, which
  `__vgic_v5_save_ppi_state()` refreshes on every exit; one byte per PPI, 5
  bits used.
