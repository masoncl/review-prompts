- `SVE_SIG_FLAG_SM`: not compared with the task's current SVCR; it selects the
  mode restored. Set: `sme_alloc()`, `SVCR_SM_MASK` and `TIF_SME` are set, VL
  must equal `task_get_sme_vl()`. Clear, with a payload: `SVCR_SM_MASK` is
  cleared and `TIF_SVE` set.
- SVE record with payload: after the copy into `sve_state`,
  `fpsimd_update_current_state()` overwrites the low 128 bits of every Z
  register with the V registers of the `fpsimd_context` record; FPSR and FPCR
  come from that record too.
- VL test: made before the header-only test, so a header-only record must also
  carry the task's current SVE VL; `preserve_sve_context()` writes the VL even
  when there is no payload.
- Size rejections in `restore_sve_fpsimd_context()`: both are `<`; a record
  larger than `SVE_SIG_CONTEXT_SIZE()` for the VL is accepted.
  `preserve_sve_context()` writes the size rounded up to 16.
- Record without `SVE_SIG_FLAG_SM`: the feature test is
  `system_supports_sve()` or `system_supports_sme()`; there is no test of
  `system_supports_sve()` alone.
- SVE record in a written frame: always present when SVE or SME is supported;
  it has a payload when `thread.fp_type == FP_STATE_SVE` or streaming mode is
  on, and `TIF_SVE` is not consulted.
- ZA record in a written frame: always present when SME is supported,
  header-only when ZA is off; the ZT record is present only with SME2 and ZA
  on.
- GCS record in a written frame: present when `system_supports_gcs()` and
  `current->thread.gcspr_el0` is non-zero.
