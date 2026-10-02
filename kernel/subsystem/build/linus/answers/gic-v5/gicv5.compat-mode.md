- Cpucap: `ARM64_HAS_GICV5_LEGACY`, matched per CPU by
  `test_has_gicv5_legacy()` from `ICC_IDR0_EL1_GCIE_LEGACY`.
- Host type in this mode: `kvm_vgic_global_state.type` is `VGIC_V5`, so a test
  for `VGIC_V3` is false; `vgic_host_has_gicv3()` in
  `arch/arm64/kvm/vgic/vgic.h` covers both hosts.
- `vgic_v3_deactivate_phys()` in `arch/arm64/kvm/vgic/vgic-v3.c`: issues
  `gic_insn(..., CDDI)` when `ARM64_HAS_GICV5_LEGACY` is set, else
  `gic_write_dir()`.
- CDDI type field: hard-coded to 1, which is `GICV5_HWIRQ_TYPE_PPI`; the
  physical interrupt is assumed to be a PPI.
- When `vgic_v3_deactivate_phys()` runs: only for a HW-mapped interrupt
  that is not in a list register (EOIcount replay in
  `vgic_v3_fold_lr_state()`, trapped DIR write in `vgic_v3_deactivate()`).
- Interrupt in a list register: `vgic_v3_compute_lr()` still sets `ICH_LR_HW`
  on a GICv5 host, and KVM issues no CDDI for it; deactivation is left to the
  hardware.
