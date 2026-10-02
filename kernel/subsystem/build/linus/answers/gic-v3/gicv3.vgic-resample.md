- Callers of `vgic_irq_handle_resampling()`: `vgic_v3_fold_lr()` and
  `vgic_v2_fold_lr()`, not the fold-state functions directly.
- Those two are also reached from `vgic_v3_deactivate()`,
  `vgic_v2_deactivate()` and the `eoicount` replay loop, with an LR value
  built by `vgic_v3_compute_lr()` or `vgic_v2_compute_lr()`.
- GICv5 VM: `vgic_fold_state()` calls `vgic_v5_fold_ppi_state()` and never
  reaches `vgic_irq_handle_resampling()`.
- Re-read condition without software resampling: only when
  `lr_pending || (lr_deactivated && irq->line_level)`, not on every EOI.
- `vgic_get_phys_line_level()` without `get_input_level()`: reads
  `IRQCHIP_STATE_PENDING` of `irq->host_irq`; it does not fall back to
  `irq->line_level`.
- `irq->line_level`: set to false by `vgic_v3_populate_lr()` and
  `vgic_v2_populate_lr()` when a mapped level interrupt goes into the LR
  as pending; that is why a still-pending LR forces a re-read.
- Software resampling in `vgic_irq_handle_resampling()`: the line is not read
  and `lr_deactivated` and `lr_pending` are ignored; physical active is
  cleared whenever `!(irq->active || irq->pending_latch)`.
- `ICH_LR_HW` and `GICH_LR_HW`: left out for a software-resampled interrupt
  by `vgic_v3_compute_lr()` and `vgic_v2_compute_lr()`.
- Second re-read site: `vgic_mmio_write_senable()` re-reads a mapped level
  line on guest enable and clears physical active if
  `!irq->active && was_high && !irq->line_level`.
