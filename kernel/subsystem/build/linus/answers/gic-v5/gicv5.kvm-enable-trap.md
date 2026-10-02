- Second bank (`ICC_PPI_ENABLER1_EL1`, odd `p->Op2`): the write is discarded;
  `access_gicv5_ppi_enabler()` returns `true` before it stores or masks
  anything.
- Storage: `vgic_ppi_enabler` in `struct vgic_v5_cpu_if` holds
  `VGIC_V5_NR_PRIVATE_IRQS` (64) bits; there is no second-bank shadow and no
  second mask.
- First bank: the shadow is replaced by `p->regval` ANDed with the mask; the
  previous shadow value is not kept, although the comment says "merge".
- Mask: `vgic_ppi_mask` in `struct vgic_v5_vm`, one per VM, filled by
  `vgic_v5_finalize_ppi_state()` in `arch/arm64/kvm/vgic/vgic-v5.c`.
- After the store: `irq->enabled` is set from the shadow for every PPI in the
  mask, each under `irq->irq_lock`; `vgic_v5_has_pending_ppi()` reads
  `irq->enabled`.
- Hardware: the handler writes no register. `__vgic_v5_restore_ppi_state()` in
  `arch/arm64/kvm/hyp/vgic-v5-sr.c` writes the shadow to
  `SYS_ICH_PPI_ENABLER0_EL2` and the constant 0 to `SYS_ICH_PPI_ENABLER1_EL2`.
- Exit: `__vgic_v5_save_ppi_state()` does not read the enable registers back;
  no code reads `SYS_ICH_PPI_ENABLER0_EL2`.
- Reads: not trapped for a GICv5 guest; `__compute_ich_hfgwtr()` forces only
  the write trap.
- A read that reaches the handler: `WARN_ON_ONCE()`, then `undef_access()`.
