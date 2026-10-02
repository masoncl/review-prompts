- PPIs per vCPU: 64, `VGIC_V5_NR_PRIVATE_IRQS` in `include/kvm/arm_vgic.h`,
  not 128; only the architected half is supported.
- `__vgic_v5_save_ppi_state()`: has `BUILD_BUG_ON(VGIC_V5_NR_PRIVATE_IRQS !=
  64)`; raising the count needs the hyp code changed too.
- PPIs that can be exposed: at most six, those in `impl_ppi_mask`; see
  `vgic_v5_get_implemented_ppis()` in `arch/arm64/kvm/vgic/vgic-v5.c`.
- `vgic_get_vcpu_irq()`: gates on `__irq_is_ppi()`, then has both an explicit
  range test that returns `NULL` and `array_index_nospec()`.
- An ID that fails the gate (bare ID, other type, PPI ID of 64 or more):
  falls through to `vgic_get_irq()`, which returns `NULL` for every ID of a
  GICv5 guest.
