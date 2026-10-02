- `local_daif_mask()`: sets D, A, I, F first, then under
  `system_uses_irq_prio_masking()` writes
  `GIC_PRIO_IRQON | GIC_PRIO_PSR_I_SET` to PMR.
- `local_daif_mask()` entry check: WARNs only when PMR already equals
  `GIC_PRIO_IRQOFF | GIC_PRIO_PSR_I_SET`, and only under
  `system_has_prio_mask_debugging()`.
- `local_daif_mask()` with IRQs already masked by PMR: accepted;
  `arm64_exit_to_user_mode()` calls it after `local_irq_disable()`.
- `local_daif_restore()` with I set in `flags`, priority masking on:

| `flags` | PMR written | DAIF written |
|---|---|---|
| I set, A clear | `GIC_PRIO_IRQOFF` | `flags` with I and F cleared |
| I set, A set | `GIC_PRIO_IRQON \| GIC_PRIO_PSR_I_SET` | `flags` unchanged |

- `local_daif_restore()` under priority masking: never leaves DAIF.I set with
  DAIF.A clear.
- `local_daif_save()` then `local_daif_restore()` under priority masking,
  entered with DAIF = I|F and PMR = `GIC_PRIO_IRQON | GIC_PRIO_PSR_I_SET`:
  returns with DAIF I and F clear and PMR = `GIC_PRIO_IRQOFF`, the state
  `gic_unmask_pnmis()` sets.
- `local_daif_inherit()`: writes `regs->pmr` to PMR whenever
  `system_uses_irq_prio_masking()`, whatever the interrupted context's IRQ
  state; only `trace_hardirqs_on()` depends on `regs_irqs_disabled()`.
- `local_daif_inherit()`: has no WARN of its own and does not call
  `local_daif_restore()`.
- `local_daif_inherit()` callers: only the EL1 synchronous handlers in
  `arch/arm64/kernel/entry-common.c`, straight after
  `arm64_enter_from_kernel_mode()`; there is no enter_from_kernel_mode() here.
- **Unsafe usage**: calling `local_daif_restore()` with DAIF.I or DAIF.F
  clear.
  - Unsafe: under priority masking the PMR write lands while DAIF.I is still
    clear; the WARN at the top of `local_daif_restore()` checks this, under
    `system_has_prio_mask_debugging()` only.
  - Safe: after `local_daif_save()` or `local_daif_mask()`, as `cpu_suspend()`
    in `arch/arm64/kernel/suspend.c` does.
  - Safe: straight after exception entry, as `el0_da()` does.
  - Safe: with DAIF still masked from boot, as `secondary_start_kernel()`
    does.
- **Unsafe usage**: passing a `local_irq_save()` or `arch_local_save_flags()`
  value to `local_daif_restore()`.
  - Unsafe: under priority masking the value is a PMR priority, and
    `local_daif_restore()` decodes `PSR_I_BIT` and `PSR_A_BIT` from it.
  - Safe: a value from `local_daif_save()` or `local_daif_save_flags()`, as
    `__cpu_replace_ttbr1()` in `arch/arm64/mm/mmu.c` does.
  - Safe: a `DAIF_PROCCTX`, `DAIF_PROCCTX_NOIRQ` or `DAIF_ERRCTX` constant, as
    `el1h_64_error_handler()` does.
