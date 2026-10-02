- Checks in both handlers, in order: `addr & 4` set, then
  `!vgic_lpis_enabled()`; either one drops the write.
- `vgic_has_its()`: not called by either handler.
- `vgic_lpis_enabled()`: tests `ctlr == GICR_CTLR_ENABLE_LPIS`, so a write
  that arrives while `ctlr` holds `GICR_CTLR_RWP` (disable in progress) is
  dropped too.
- `vgic_mmio_write_invlpi()` extra check: `lower_32_bits(val) < VGIC_MIN_LPI`
  drops the write before the busy counter is touched; without it
  `vgic_get_irq()` could return an SPI.
- `vgic_set_rdist_busy()`: brackets the work in both handlers; `syncr_busy`
  in `struct vgic_cpu` is an `atomic_t` counter, not a flag.
- `vgic_mmio_write_invlpi()` work: `vgic_its_inv_lpi()`, which is
  `update_lpi_config()` with no vCPU filter; `priority` and `enabled` of the
  LPI are reloaded whichever vCPU it targets.
- `vgic_mmio_write_invall()` work: `vgic_its_invall()` passes the vCPU as
  filter; `priority` and `enabled` change only for LPIs whose `target_vcpu` is
  this redistributor's vCPU.
- ITS translation cache: not touched; neither path calls
  `vgic_its_invalidate_cache()`.
