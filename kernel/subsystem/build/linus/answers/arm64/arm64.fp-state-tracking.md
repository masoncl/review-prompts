- `TIF_FOREIGN_FPSTATE` clear: the registers hold the state that this CPU's
  `fpsimd_last_state` describes; `fpsimd_save_user_state()` decides whether
  to save from the flag alone and saves through `fpsimd_last_state`, never
  through `current->thread`.
- Between `kvm_arch_vcpu_ctxsync_fp()` and `kvm_arch_vcpu_put_fp()`, when
  `guest_owns_fp_regs()`: the flag is clear on the host task while
  `fpsimd_last_state` describes the vCPU, so a softirq's `kernel_neon_begin()`
  saves guest registers into the vCPU.
- `kvm_arch_vcpu_load_fp()`: saves and flushes the host task's state at once
  with `fpsimd_save_and_flush_cpu_state()` and sets `fp_owner` to
  `FP_STATE_FREE`; the host state is not kept live. With `IN_NESTED_ERET` or
  `IN_NESTED_EXCEPTION` set it returns before both.
- `kvm_arch_vcpu_ctxsync_fp()`: when `guest_owns_fp_regs()`, binds the vCPU's
  state with `fpsimd_bind_state_to_cpu()` and clears `TIF_FOREIGN_FPSTATE`.
- `kvm_arch_vcpu_ctxflush_fp()`: runs before guest entry; if
  `TIF_FOREIGN_FPSTATE` is set it sets `fp_owner` to `FP_STATE_FREE`.
- `fpsimd_flush_task_state()`: sets `fpsimd_cpu` to `NR_CPUS` and sets
  `TIF_FOREIGN_FPSTATE` on the task it is given, current or not; it also sets
  `thread.kernel_fpsimd_state` to NULL.
- `fpsimd_flush_cpu_state()`: static to `arch/arm64/kernel/fpsimd.c`; besides
  clearing `fpsimd_last_state.st` it runs `sme_smstop()`, which
  `kvm_arch_vcpu_load_fp()` relies on.
- `fpsimd_update_current_state()`: only writes `thread.uw.fpsimd_state` and,
  for `FP_STATE_SVE`, calls `fpsimd_to_sve()`; it loads no register and
  changes no flag, so its callers save and flush first, as
  `restore_sigframe()` does.
- `struct cpu_fp_state` holds copies of the `sve_state` and `sme_state`
  pointers and of both VLs, taken at bind time; code that allocates a buffer
  while the state is live must rebind, as `do_sve_acc()` and `do_sme_acc()`
  do with `fpsimd_bind_task_to_cpu()`.
