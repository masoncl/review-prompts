- Values: `GIC_PRIO_IRQON` is `GICV3_PRIO_UNMASKED` (0xe0), `GIC_PRIO_IRQOFF`
  is `GICV3_PRIO_IRQ` (0xc0), `GIC_PRIO_PSR_I_SET` is `GICV3_PRIO_PSR_I_SET`
  (0x10); see `include/linux/irqchip/arm-gic-v3-prio.h`, which also has
  `GICV3_PRIO_NMI` (0x80).
- `arch_local_save_flags()` under priority masking: returns the raw PMR;
  nothing ORs in `GIC_PRIO_PSR_I_SET` at save time.
- `GIC_PRIO_PSR_I_SET` in a flags value or in `regs->pmr`: present only
  because a writer put it in PMR, for example `kernel_entry` in
  `arch/arm64/kernel/entry.S` or `local_daif_mask()`.
- `arch_local_irq_save()` under priority masking: writes nothing when PMR is
  not `GIC_PRIO_IRQON`; it returns the current PMR and leaves it. See
  `__pmr_local_irq_save()`.
- `arch_local_irq_enable()` and `arch_local_irq_disable()` under priority
  masking, with PMR neither `GIC_PRIO_IRQON` nor `GIC_PRIO_IRQOFF`:
  `WARN_ON_ONCE()` under `CONFIG_ARM64_DEBUG_PRIORITY_MASKING`; the PMR write
  still happens and DAIF is not touched.
- `arch_irqs_disabled()` under priority masking: reads only PMR, never DAIF;
  see `__pmr_irqs_disabled()`.
- `local_daif_save_flags()` in `arch/arm64/include/asm/daifflags.h`: the
  helper that reads both DAIF and PMR.
- `regs_irqs_disabled()`: tests `PSR_I_BIT` in `regs->pstate` under both
  schemes, and additionally `regs->pmr != GIC_PRIO_IRQON` under priority
  masking.
- `flags & PSR_I_BIT` on a PMR-format flags value: always true, because 0xe0,
  0xc0 and 0xf0 all contain 0x80; the test reads "masked" even when PMR is
  `GIC_PRIO_IRQON`.
- **Potentially unsafe usage**: reading `regs->pmr` directly.
  - Unsafe: without `system_uses_irq_prio_masking()`; `kernel_entry` branches
    over the store to `S_PMR`, so the field was not written at entry.
  - Safe: behind `system_uses_irq_prio_masking()`, as
    `irqs_priority_unmasked()` in `arch/arm64/include/asm/ptrace.h` and
    `local_daif_inherit()` do.
