- `task_smstop_sm()`: when SM is set in `thread.svcr`, zeroes the saved V
  registers, sets the saved FPSR to 0x0800009f, zeroes `thread.uw.fpmr` if
  `system_supports_fpmr()`, clears `SVCR_SM_MASK` and sets `thread.fp_type` to
  `FP_STATE_FPSIMD`.
- `task_smstop_sm()` leaves alone: `TIF_SVE`, `TIF_SME`, FPCR, the ZA enable,
  `sve_state`, `sme_state` and the registers.
- `task_smstop_sm()` acts on the saved state only; the task's state must not
  be live when it is called.
- Callers of `task_smstop_sm()`: `setup_return()` and
  `arch_dup_task_struct()`; ptrace does not use it, `sve_set_common()` clears
  the bit itself and rewrites the whole state.
