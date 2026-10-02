- Models take `fpsimd_flush_cpu_state()` to clear only the binding and set
  `TIF_FOREIGN_FPSTATE`. Its `sme_smstop()` leaves `PSTATE.SM` and
  `PSTATE.ZA` clear after `kernel_neon_begin()` and
  `fpsimd_save_and_flush_cpu_state()`, when SME is supported; see
  `arch/arm64/kernel/fpsimd.c`.
- Models take `__get_user()` and `__put_user()` to skip `access_ok()`.
  `__raw_get_user()` and `__raw_put_user()` in
  `arch/arm64/include/asm/uaccess.h` do neither `access_ok()` nor the mask.
- Models take exit to EL0 to save the shadow call stack pointer. `scs_save`
  (`arch/arm64/include/asm/scs.h`) is only in `cpu_switch_to()` and
  `call_on_irq_stack()`.
- Models take the order of `arch/arm64/tools/cpucaps` to be cosmetic.
  `arch/arm64/tools/gen-cpucaps.awk` numbers names in file order, and
  `cpu_enable_sme2()` and `cpu_enable_fa64()` have a `BUILD_BUG_ON()` on
  their number against `ARM64_SME`.
- Models take `do_notify_resume()` to be arm64's return-to-user work loop.
  The generic loop calls `arch_exit_to_user_mode_work()` in
  `arch/arm64/include/asm/entry-common.h` and `arch_do_signal_or_restart()`
  in `arch/arm64/kernel/signal.c`.
