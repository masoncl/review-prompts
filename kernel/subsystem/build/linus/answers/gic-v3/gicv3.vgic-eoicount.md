- `ICH_HCR_EL2_EOIcount` in `cpuif->vgic_hcr`: `__vgic_v3_save_state()` in
  `arch/arm64/kvm/hyp/vgic-v3-sr.c` copies it from hardware only when
  `ICH_HCR_EL2_LRENPIE` is set in `vgic_hcr`.
- Count starts at 0 on each entry: `vgic_v3_configure_hcr()` rewrites
  `vgic_hcr`.
- Walk start: `list_for_each_entry_continue()` from `last_lr_irq`, so the
  first entry looked at is the one after it.
- Why there: every entry that was in an LR is at or before `last_lr_irq`, and
  was folded from the real LR value just before the walk.
- Per matched entry: `vgic_v3_compute_lr()` with `ICH_LR_ACTIVE_BIT` cleared
  is passed to `vgic_v3_fold_lr()`; `irq->active` is not cleared directly, so
  fold's notification and resampling apply.
- Hardware-backed entry: `vgic_v3_deactivate_phys()` when the pseudo-LR has
  `ICH_LR_HW`; it uses `gic_write_dir()`, or the GICv5 CDDI instruction with
  `ARM64_HAS_GICV5_LEGACY`.
- `vgic_v3_fold_lr_state()` does not call `irq_set_irqchip_state()` or
  `vgic_irq_set_phys_active()` itself.
- Mapped level `vgic_irq_needs_resampling()` interrupt: pseudo-LR has no
  `ICH_LR_HW`; physical active is cleared inside fold by
  `vgic_irq_handle_resampling()`.
