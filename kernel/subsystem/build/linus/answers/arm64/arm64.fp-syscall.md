- `fpsimd_syscall_enter()`: changes no thread flag and no saved state;
  `TIF_SVE` and `TIF_FOREIGN_FPSTATE` are left as they are.
- `TIF_SVE` afterwards: stays set if the state stays live for the whole
  syscall; if the state is saved and reloaded, `task_fpsimd_load()` sees
  `FP_STATE_FPSIMD` and clears it, and the next SVE use traps to
  `do_sve_acc()`.
- Streaming mode: `sme_smstop_sm()` at entry whenever
  `system_supports_sme()`; the ZA enable and ZA contents are kept.
- `sme_smstop_sm()` changes only the live SVCR; `thread.svcr` of `current`
  is not updated until the next `fpsimd_save_user_state()`.
- `fpsimd_syscall_exit()`: only writes `FP_STATE_CURRENT` to
  `fpsimd_last_state.to_save`; it loads nothing. `el0_svc()` calls it after
  `arm64_syscall_exit_to_user_mode()`, which is where a pending reload runs.
