- `get_cpu_fpsimd_context()` and `put_cpu_fpsimd_context()`: static to
  `arch/arm64/kernel/fpsimd.c`; code elsewhere uses wrappers such as
  `fpsimd_save_and_flush_current_state()`, or runs with IRQs disabled as
  `kvm_arch_vcpu_ctxsync_fp()` does.
- Not `CONFIG_PREEMPT_RT`, IRQs disabled: `get_cpu_fpsimd_context()` does
  nothing; it calls `local_bh_disable()` only when `irqs_disabled()` is false.
- `put_cpu_fpsimd_context()`, not `CONFIG_PREEMPT_RT`: tests
  `irqs_disabled()` again, so the IRQ state must be the same at get and at
  put.
- There is no have_cpu_fpsimd_context() helper and no per-CPU busy flag in
  this tree.
- How callees state the assumption:

  | Function | Check |
  |---|---|
  | `fpsimd_save_user_state()`, `task_fpsimd_load()` | `WARN_ON(preemptible())` |
  | `fpsimd_bind_state_to_cpu()` | `WARN_ON(!in_softirq() && !irqs_disabled())` |
  | `fpsimd_thread_switch()` | `WARN_ON_ONCE(!irqs_disabled())` |
  | `fpsimd_bind_task_to_cpu()`, `fpsimd_flush_cpu_state()` | comment only |

- `fpsimd_save_and_flush_cpu_state()`: has `WARN_ON(preemptible())` but does
  not need the caller to hold the context; it disables IRQs itself with
  `local_irq_save()`.
- `WARN_ON(preemptible())`: passes under a plain `preempt_disable()`, where
  softirqs can still run on a non-RT kernel; it does not prove the context is
  held.
- **Potentially unsafe usage**: writing the saved FP state of `current`
  (`thread.uw.fpsimd_state`, `thread.sve_state`, `thread.fp_type`,
  `thread.svcr`) without the context held.
  - Unsafe: while `TIF_FOREIGN_FPSTATE` is clear and IRQs are enabled;
    `fpsimd_save_user_state()`, run from a softirq's `kernel_neon_begin()` or
    from `fpsimd_thread_switch()`, overwrites the edit from the registers.
  - Safe: after `fpsimd_save_and_flush_current_state()`, as
    `restore_sigframe()` and `compat_restore_vfp_context()` do;
    `fpsimd_save_user_state()` returns at once while `TIF_FOREIGN_FPSTATE` is
    set, and `fpsimd_thread_switch()` keeps it set while `fpsimd_cpu` is
    `NR_CPUS`.
  - Safe: with IRQs disabled, where `get_cpu_fpsimd_context()` itself takes
    nothing on a non-RT kernel; `kvm_arch_vcpu_ctxsync_fp()` rebinds and
    clears `TIF_FOREIGN_FPSTATE` that way and asserts `irqs_disabled()`.
