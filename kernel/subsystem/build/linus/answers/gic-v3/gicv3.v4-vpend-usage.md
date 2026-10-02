- Helper: `its_clear_vpend_valid()` in `drivers/irqchip/irq-gic-v3-its.c`.
- `gicr_write_vpendbaser()`: the raw accessor, not the helper; on arm64 it is
  `writeq_relaxed()` with no polling and no erratum handling.
- `gicr_write_vpendbaser()` on 32-bit Arm
  (`arch/arm/include/asm/arch_gicv3.h`): if Valid reads set in the register
  it first clears Valid with a 32-bit write, then writes the low word, then
  the high word.
- The helper changes other bits in the same write that clears Valid: it
  applies `clr` and `set` to the value, as `its_vpe_4_1_deschedule()` uses
  for `GICR_VPENDBASER_4_1_DB`.
- `its_cpu_init_lpis()`: calls the helper only when `gic_rdists->has_vlpis`
  is set and `gic_rdists->has_rvpeid` is not.
- Writes that do not use the helper: `its_vpe_schedule()`,
  `its_vpe_4_1_schedule()`, `allocate_vpe_l1_table()`, and
  `__gic_update_rdist_properties()` in `drivers/irqchip/irq-gic-v3.c`.
- `allocate_vpe_l1_table()` and `__gic_update_rdist_properties()`: only when
  Valid reads 1, write the constant `GICR_VPENDBASER_PendingLast`; neither
  polls Dirty and neither reads a result back.
- `__gic_update_rdist_properties()`: runs from `gic_init_bases()` before
  `its_init()`, for each redistributor with `GICR_TYPER_VLPIS` and
  `GICR_TYPER_RVPEID`; it is the one write that also reaches the
  redistributors of other CPUs.
- `its_vpe_schedule()` and `its_vpe_4_1_schedule()`: neither reads the
  register nor tests Valid first; `vgic_v4_load()` calls in only when
  `vpe->resident` is false.
- **Unsafe usage**: using PendingLast read from `GICR_VPENDBASER` after
  clearing Valid, without waiting for `GICR_VPENDBASER_Dirty` to read 0.
  - Safe: take the value returned by `its_clear_vpend_valid()`, as
    `its_vpe_deschedule()` does; `read_vpend_dirty_clear()` does the wait
    and the helper forces PendingLast to 1 when Dirty never clears.
- **Unsafe usage**: calling `its_make_vpe_resident()`,
  `its_make_vpe_non_resident()` or `its_commit_vpe()` from preemptible
  context.
  - Safe: with preemption disabled, as `check_vcpu_requests()` and
    `kvm_vcpu_wfi()` do; each of the three has `WARN_ON(preemptible())`, and
    `gic_data_rdist_vlpi_base()` resolves to the current CPU's
    redistributor.
