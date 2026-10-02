- `kvm_vcpu_wfi()`: defined in `arch/arm64/kvm/arm.c`.
- Calls made: `kvm_vgic_put()` before the halt and `kvm_vgic_load()` after
  it; it does not call `vgic_v4_put()` or `vgic_v4_load()` directly.
- `IN_WFI` is also tested by `vgic_v5_put()`, which calls
  `vgic_v5_sync_ppi_priorities()` only when it is set.
- `kvm_vgic_vcpu_pending_irq()`: does not test `IN_WFI`.
