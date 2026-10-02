| Handler | How DAIF is set | Masked while the body runs | Can interrupt it |
|---|---|---|---|
| EL1 IRQ/FIQ, IRQ path: `__el1_irq()` | raw `write_sysreg(DAIF_PROCCTX_NOIRQ, daif)` in `el1_interrupt()` | I, F | debug, SError; pseudo-NMI once `gic_unmask_pnmis()` has run |
| EL1 pseudo-NMI: `__el1_pnmi()` | same write in `el1_interrupt()` | I, F | debug, SError |
| EL1 SError: `el1h_64_error_handler()` | `local_daif_restore(DAIF_ERRCTX)` | A, I, F | debug |
| EL1 debug: `el1_breakpt()`, `el1_softstp()`, `el1_watchpt()`, `el1_brk64()` | not written | D, A, I, F | nothing |
| EL0 debug: `el0_breakpt()`, `el0_watchpt()` | `local_daif_restore(DAIF_PROCCTX)` after the handler body | D, A, I, F | nothing |
| EL0 debug: `el0_softstp()`, `el0_brk64()`, `el0_bkpt32()` | `local_daif_restore(DAIF_PROCCTX)` before the handler body | none | everything |
| EL0 SError: `__el0_error_handler_common()` | `local_daif_restore(DAIF_ERRCTX)`, then `DAIF_PROCCTX` after `do_serror()` | A, I, F during `do_serror()` | debug during `do_serror()` |

- el1_dbg(): not in this tree; the four EL1 debug handlers in the table call
  `arm64_enter_el1_dbg()`.
- gic_arch_enable_irqs(): not in this tree; `gic_unmask_pnmis()` in
  `arch/arm64/include/asm/arch_gicv3.h` writes `GIC_PRIO_IRQOFF` and clears
  DAIF I and F.
- `el1_interrupt()` under priority masking: does not write PMR before the
  handler runs; it stays at the `GIC_PRIO_IRQON | GIC_PRIO_PSR_I_SET` that
  `kernel_entry` wrote until the irqchip driver changes it.
- `gic_unmask_pnmis()`: called by `__gic_handle_irq_from_irqson()` in
  `drivers/irqchip/irq-gic-v3.c` before the regular IRQ is handled; it does
  nothing without `gic_prio_masking_enabled()`.
- `el1_interrupt()` fixed mask: clears D and A whatever the interrupted
  context had, on the pseudo-NMI path too.
- `el0_softstp()`: runs `try_step_suspended_breakpoints()` fully masked, then
  unmasks before `do_el0_softstep()`.
- `arm64_exit_to_kernel_mode()`: calls `local_irq_disable()` first when
  `regs_irqs_disabled()` is false; there is no exit_to_kernel_mode() here.
- `__el1_pnmi()` and `el1h_64_error_handler()`: call `local_daif_mask()`
  themselves, before `irqentry_nmi_exit()`.
- `arch/arm64/mm/fault.c`: contains no `interrupts_enabled()` test and no
  `local_irq_enable()`; nothing in it unmasks what `el1_abort()` inherited.
