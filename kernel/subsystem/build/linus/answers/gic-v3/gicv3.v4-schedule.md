- GICv4.0 doorbell: `its_make_vpe_resident()` calls
  `disable_irq_nosync(vpe->irq)` before sending `SCHEDULE_VPE`, and does so
  even if the command then fails.
- GICv4.1 doorbell: not touched; `its_vpe_4_1_schedule()` writes
  `GICR_VPENDBASER_4_1_DB` as 0.
- `its_vpe_4_1_schedule()`: the value is exactly `GICR_VPENDBASER_Valid`,
  `GICR_VPENDBASER_4_1_VGRP0EN` from `info->g0en`,
  `GICR_VPENDBASER_4_1_VGRP1EN` from `info->g1en`, and
  `GICR_VPENDBASER_4_1_VPEID`; no address, no attributes.
- `info->req_db`: shares a union with `g0en` and `g1en` in
  `struct its_cmd_info`; only `its_vpe_4_1_deschedule()` reads it.
- `its_vpe_schedule()` on GICv4.0: the `GICR_VPENDBASER` value carries
  `GICR_VPENDBASER_PendingLast`, `GICR_VPENDBASER_IDAI` from `vpe->idai`, and
  `GICR_VPENDBASER_Valid`.
- Cacheability and shareability bits in `its_vpe_schedule()`: set in both
  `GICR_VPROPBASER` and `GICR_VPENDBASER` only when
  `rdists_support_shareable()` is true.
- `its_wait_vpt_parse_complete()`: returns without reading the register
  unless `gic_rdists->has_vpend_valid_dirty` is set; that flag is the AND of
  `GICR_TYPER_DIRTY` over the redistributors, in
  `__gic_update_rdist_properties()`.
- Timeout in `its_wait_vpt_parse_complete()`: only `WARN_ON_ONCE()`;
  `COMMIT_VPE` still returns 0, so `its_commit_vpe()` sets `vpe->ready`.
