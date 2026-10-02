- `arm64_enter_from_user_mode()`: `enter_from_user_mode()`, then
  `rseq_note_user_irq_entry()`, `mte_disable_tco_entry()`,
  `sme_enter_from_user_mode()`.
- `arm64_syscall_enter_from_user_mode()`: the same without
  `rseq_note_user_irq_entry()`; it unmasks nothing and does no syscall work.
- `el0_svc()` unmasks with `local_daif_restore(DAIF_PROCCTX)` after
  `fpsimd_syscall_enter()`.
- `sme_enter_from_user_mode()` and `sme_exit_to_user_mode()`: called by both
  enter and both exit helpers; they act only with
  `ARM64_WORKAROUND_4193714` and `TIF_SME`; see
  `arch/arm64/include/asm/fpsimd.h`.
- Syscall exit: `arm64_syscall_exit_to_user_mode()`, which calls
  `syscall_exit_to_user_mode_prepare()`; arm64 does not call
  `syscall_exit_to_user_mode()`.
- `ret_from_fork` also exits through `arm64_syscall_exit_to_user_mode()`,
  via `asm_exit_to_user_mode()`.
- `fpsimd_syscall_enter()`: static in `arch/arm64/kernel/entry-common.c`,
  called from `el0_svc()` only; `el0_svc_compat()` does not call it.
- `fpsimd_syscall_enter()` leaves streaming mode with `sme_smstop_sm()` and
  keeps ZA; with `TIF_SVE` it calls `sve_flush_live()`.
- `arm64_syscall_exit_to_user_mode()` ends with `exit_to_user_mode()`, so
  `fpsimd_syscall_exit()`, which `el0_svc()` calls after it, runs after
  `exit_to_user_mode()`.
- rseq fixup: there is no rseq_handle_notify_resume; `TIF_RSEQ` is
  `TIF_NOTIFY_RESUME` on arm64, and `resume_user_mode_work()` calls
  `rseq_handle_slowpath()`.
- `rseq_exit_to_user_mode_restart()`: a stub returning `false` without
  `CONFIG_GENERIC_ENTRY`, which arm64 does not select.
- rseq on exit: `rseq_irqentry_exit_to_user_mode()` or
  `rseq_syscall_exit_to_user_mode()`, from the two prepare functions;
  neither does a fixup. The first clears `current->rseq.event.events`, the
  second does so only under `CONFIG_LOCKDEP`.
- **Unsafe usage**: `arm64_syscall_enter_from_user_mode()` or
  `fpsimd_syscall_enter()` on an EL0 path that is not an SVC.
  - Unsafe: `user_irq` stays clear, and for an `rseq_v2()` task
    `rseq_sched_switch_event()` acts only on `user_irq` or `ids_changed`
    and `rseq_signal_deliver()` only on `user_irq`; live SVE and streaming
    state is discarded.
  - Safe: `arm64_enter_from_user_mode()` for every other EL0 exception, as
    `el0_da()` and `el0_interrupt()` do.
