- Selection: `gic_handle_irq()` runs `__gic_handle_irq_from_irqsoff()` when
  `gic_supports_nmi() && !interrupts_enabled(regs)`, otherwise
  `__gic_handle_irq_from_irqson()`.
- `interrupts_enabled()` in `arch/arm64/include/asm/ptrace.h`: false when
  `PSR_I_BIT` is set in the saved pstate or, with
  `system_uses_irq_prio_masking()`, the saved `pmr` is not exactly
  `GIC_PRIO_IRQON`.

| Path | NMI decision | PMR around the acknowledge |
|---|---|---|
| `__gic_handle_irq_from_irqson()` | `gic_rpr_is_nmi_prio()` after the IAR read | untouched before; `gic_unmask_pnmis()` afterwards |
| `__gic_handle_irq_from_irqsoff()` | none; RPR is not read, the result always goes to `__gic_handle_nmi()` | saved, `gic_pmr_mask_irqs()`, `isb()`, IAR read, saved value written back |

- There is no gic_arch_enable_irqs() in this tree; `gic_unmask_pnmis()` in
  `arch/arm64/include/asm/arch_gicv3.h` writes `GIC_PRIO_IRQOFF` to the PMR
  and clears DAIF.I and DAIF.F.
- `gic_unmask_pnmis()`: tests `gic_prio_masking_enabled()`, not
  `gic_supports_nmi()`, so it also runs when NMIs are forbidden; it is an
  empty stub in `arch/arm/include/asm/arch_gicv3.h`.
- `gic_unmask_pnmis()` in the irqson path: runs in both cases, after
  `nmi_exit()` for an NMI and before `__gic_handle_irq()` for a regular
  interrupt.
- Special IDs in the irqson path: `gic_rpr_is_nmi_prio()` and
  `gic_unmask_pnmis()` run before `gic_irqnr_is_special()` is tested inside
  `__gic_handle_irq()`.
