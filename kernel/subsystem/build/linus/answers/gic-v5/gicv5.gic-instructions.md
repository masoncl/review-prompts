- The table has only the instructions where this tree differs from the usual
  picture, and covers kernel code only, not `tools/`.

| Instruction | Issued as | Only issued from | Easy to miss |
|---|---|---|---|
| CDEOI | `gic_insn(0, CDEOI)` | `gicv5_handle_irq()` | not issued by `gicv5_hwirq_eoi()` or any `irq_eoi` |
| CDDI | `gic_insn(cddi, CDDI)` | `gicv5_hwirq_eoi()`; `vgic_v3_deactivate_phys()` in `arch/arm64/kvm/vgic/vgic-v3.c` | the KVM site runs under `ARM64_HAS_GICV5_LEGACY` and hard-codes type 1 (PPI) |
| CDAFF | `gic_insn(cdaff, CDAFF)` | `gicv5_iri_irq_set_affinity()` | `gicv5_hwirq_init()` does not issue it; it issues CDPRI only |
| CDHM | `gic_insn(cdhm, CDHM)` | `gicv5_lpi_config_reset()` | LPI only, always HM 0 (edge) |
| CDNMIA | never issued | - | outside `tools/`, `GICV5_OP_GICR_CDNMIA` is used only in the trap table in `arch/arm64/kvm/emulate-nested.c` |
