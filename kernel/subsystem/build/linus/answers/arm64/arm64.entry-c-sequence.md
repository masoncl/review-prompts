- `arch/arm64/Kconfig` selects `GENERIC_IRQ_ENTRY` only, not `GENERIC_ENTRY`:
  the helpers are arm64's own, built from pieces of
  `include/linux/irq-entry-common.h`.
- arm64 calls neither `irqentry_enter()` nor `irqentry_exit()`.

| Case | arm64 helper | Built on |
|---|---|---|
| from kernel | `arm64_enter_from_kernel_mode()` | `irqentry_enter_from_kernel_mode()` |
| to kernel | `arm64_exit_to_kernel_mode()` | picks by `regs_irqs_disabled(regs)` |
| to kernel, may preempt | `arm64_exit_to_kernel_mode_preempt()` | `irqentry_exit_to_kernel_mode_preempt()` |
| to kernel, last step | `__arm64_exit_to_kernel_mode()` | `irqentry_exit_to_kernel_mode_after_preempt()` |
| to user | `arm64_exit_to_user_mode()` | `irqentry_exit_to_user_mode_prepare()`, `exit_to_user_mode()` |
| NMI | none | `irqentry_nmi_enter()`, `irqentry_nmi_exit()` |
| EL1 debug | `arm64_enter_el1_dbg()`, `arm64_exit_el1_dbg()` | open-coded |

- arm64_enter_nmi and arm64_exit_nmi do not exist; `__el1_pnmi()` and
  `el1h_64_error_handler()`, for example, call the generic NMI pair directly.
- exit_to_user_mode_prepare and exit_to_user_mode_prepare_legacy are defined
  nowhere; arm64 has no `do_notify_resume()`; pending work runs in
  `exit_to_user_mode_loop()` in `kernel/entry/common.c`.
- `local_daif_mask()`: done inside `__arm64_exit_to_kernel_mode()` and
  `arm64_exit_to_user_mode()`; a handler such as `el1_abort()` goes from
  `do_mem_abort()` straight into the exit helper.
- `irqentry_nmi_exit()` does not mask; `__el1_pnmi()` calls
  `local_daif_mask()` before it.
- Preemption on return to kernel: also after synchronous exceptions, since
  `arm64_exit_to_kernel_mode()` takes the preempt variant when the
  interrupted context had IRQs enabled.
- `__el1_irq()` calls `arm64_exit_to_kernel_mode_preempt()` directly.
- `instrumentation_begin()`: not used anywhere under `arch/arm64`; `noinstr`
  handlers call instrumentable `do_*()` functions directly between the
  helpers.
- **Potentially unsafe usage**: clearing DAIF bits before the enter helper.
  - Unsafe: clearing I or F on an entry from EL0 before
    `enter_from_user_mode()`; a nested IRQ reaches
    `irqentry_enter_from_kernel_mode()`, which calls `ct_irq_enter()` only
    for the idle task or `arch_in_rcu_eqs()`.
  - Safe: clearing only D and A with a raw `write_sysreg()`, as
    `el1_interrupt()` does with `DAIF_PROCCTX_NOIRQ`; debug and SError
    entries use `arm64_enter_el1_dbg()` and `irqentry_nmi_enter()`, which
    call `ct_nmi_enter()`.
