- `change_live_vector_length()`: after saving the live state, keeps
  `thread.fp_type`, `TIF_SVE`, `TIF_SME` and the SM bit of `thread.svcr`; the
  state is not converted to `FP_STATE_FPSIMD`.
- Vector contents after the change: V0-V31, FPSR and FPCR are preserved; with
  `FP_STATE_SVE` the new `sve_state` holds the V registers zero-padded at
  `thread_get_cur_vl()`, so the upper Z bits, P and FFR are zero.
- `thread.sve_state`: replaced by a new zeroed buffer on every change, SVE or
  SME, sized by `__sve_state_size()` for the larger of the two VLs; it does
  not call `sve_free()`.
- SME VL change: clears only `SVCR_ZA_MASK` and replaces `sme_state` with a
  zeroed buffer, so ZA and ZT0 are lost; streaming mode is kept.
- SVE VL change: leaves `sme_state` and the ZA enable alone.
- The new buffers are allocated before anything is changed; `-ENOMEM` leaves
  the task as it was.
- Live state: `fpsimd_save_and_flush_current_state()` for `current`,
  `fpsimd_flush_task_state()` for another task, so the registers are reloaded
  from memory before the task next runs in userspace.
- VL picked by `find_supported_vector_length()` equal to the current VL:
  `change_live_vector_length()` is not called and nothing is flushed.
- Callers must be able to sleep: the buffers are allocated with `GFP_KERNEL`.
- The task must be `current` or not running; for another task nothing saves
  its registers. In-tree callers pass `current` (prctl) or a ptrace target.
- The VL in effect afterwards may differ from the request:
  `find_supported_vector_length()` picks a supported one, and with
  `PR_SVE_SET_VL_ONEXEC` the current VL is unchanged. `sve_set_common()`
  re-reads `task_get_vl()` and returns `-EIO` if register data was supplied
  for another VL.
- **Potentially unsafe usage**: writing `SVCR_SM_MASK` in a task's
  `thread.svcr`.
  - Unsafe: when the saved vector state is left as it was;
    `thread_get_cur_vl()` switches between the SVE and SME VL with that bit,
    and `preserve_sve_context()` copies `sve_state` at that VL whenever the
    bit is set, whatever `thread.fp_type` says.
  - Unsafe: while the task's state is live; `fpsimd_save_user_state()`
    overwrites `thread.svcr` from the SVCR register.
  - Safe: leaving streaming mode with `task_smstop_sm()` on a task whose state
    is saved and flushed, as `setup_return()` does.
  - Safe: replacing the whole vector state, as `sve_set_common()` and
    `restore_sve_fpsimd_context()` do: flush first, `sve_alloc()` with flush,
    set `thread.fp_type`, and when entering streaming mode `sme_alloc()` and
    `TIF_SME`.
