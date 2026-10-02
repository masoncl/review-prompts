- `thread.fp_type` in `struct thread_struct`: says whether the saved vector
  state is in `thread.uw.fpsimd_state` or in `thread.sve_state`; `fp_type` in
  `struct cpu_fp_state` is a pointer to it (for a vCPU, to
  `vcpu->arch.fp_type`).
- `TIF_SVE` set with `thread.fp_type == FP_STATE_FPSIMD`: a valid state, left
  for example by a save made while `to_save` was `FP_STATE_FPSIMD`;
  `task_fpsimd_load()` then clears `TIF_SVE` and loads
  `thread.uw.fpsimd_state`, not `sve_state`.
- `TIF_SME` set: `thread.sve_state` and `thread.sme_state` must both be
  allocated; `fpsimd_save_user_state()` writes `sve_state` with no NULL test
  when the live SVCR has SM set; see `do_sme_acc()`.
- `FP_STATE_CURRENT` in `to_save`: what `fpsimd_bind_task_to_cpu()` sets for an
  ordinary task; `kvm_arch_vcpu_ctxsync_fp()` sets `FP_STATE_SVE` or
  `FP_STATE_FPSIMD` from `vcpu_has_sve()`.
- `to_save` in `struct cpu_fp_state`: set when a state is bound, and rewritten
  outside `arch/arm64/kernel/fpsimd.c` by `fpsimd_syscall_enter()` and
  `fpsimd_syscall_exit()` in `arch/arm64/kernel/entry-common.c`;
  `fpsimd_save_user_state()` only reads it.
