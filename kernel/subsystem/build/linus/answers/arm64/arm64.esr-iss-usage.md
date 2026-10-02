- `do_mem_abort()`: does not test the EC before it indexes `fault_info[]` by
  `ESR_ELx_FSC`. The EC is established by the `switch` in the sync handlers of
  `arch/arm64/kernel/entry-common.c`, for example `el0t_64_sync_handler()`.
- Helpers that test the EC themselves: `esr_is_data_abort()`,
  `esr_is_cfi_brk()`.
- Helpers that test no EC: `esr_brk_comment()`, `esr_is_ubsan_brk()`, and the
  FSC helpers such as `esr_fsc_is_translation_fault()`.
- `kvm_vcpu_dabt_get_as()`, `kvm_vcpu_dabt_get_rd()`, `kvm_vcpu_dabt_issext()`,
  `kvm_vcpu_dabt_issf()`, `kvm_vcpu_dabt_iswrite()`: test neither the EC nor
  `ESR_ELx_ISV`; that is left to the caller.
- Bit 24 has four names: `ESR_ELx_ISV` (data abort), `ESR_ELx_CV` (trapped
  conditional instruction), `ESR_ELx_IDS` (SError),
  `ESR_ELx_MOPS_ISS_MEM_INST` (MOPS).
- **Potentially unsafe usage**: applying a field macro or an EC-less helper to
  a syndrome whose class the function has not tested.
  - Unsafe: when the function can be reached with a class in which the bits
    are another field; a data abort with `ESR_ELx_ISV` set reads as
    `ESR_ELx_CV` set.
  - Safe: the function tests the class first, as `kvm_condition_valid32()`
    does before `kvm_vcpu_get_condition()`, and `nvhe_hyp_panic_handler()`
    does before `esr_is_ubsan_brk()`.
  - Safe: every caller has tested the class. `cp15_cond_valid()` reads
    `ESR_ELx_CV` before the `switch` in `do_el0_cp15()`;
    `el0t_32_sync_handler()` reaches it only for `ESR_ELx_EC_CP15_32` and
    `ESR_ELx_EC_CP15_64`. `call_el1_break_hook()` is reached only under
    `ESR_ELx_EC_BRK64`.
- **Potentially unsafe usage**: reading a qualified field without its
  qualifier.
  - Unsafe: when no caller has tested the qualifier; the field is then
    whatever the hardware left there.
  - Safe: `ESR_ELx_ISV` before `ESR_ELx_SAS`, `ESR_ELx_SSE`,
    `ESR_ELx_SRT_MASK` and `ESR_ELx_SF`, as `io_mem_abort()` and
    `kvm_hyp_handle_dabt_low()` do.
  - Safe: `kvm_handle_mmio_return()` reads them without a test, because
    `vcpu->mmio_needed` is set only by `io_mem_abort()` after its ISV test.
  - Safe: `ESR_ELx_S1PTW`, then instruction abort, then `ESR_ELx_WNR`, as
    `kvm_is_write_fault()` does.
  - Safe: a permission fault before `ESR_ELx_FSC_LEVEL`, as
    `kvm_vcpu_trap_get_perm_fault_granule()` enforces with `BUG_ON()`.
  - Safe: `ESR_ELx_FP_EXC_TFV` before the FP exception bits, as
    `do_fpsimd_exc()` does.
- **Potentially unsafe usage**: classifying a fault with
  `(fsc & ESR_ELx_FSC_TYPE)`.
  - Unsafe: for translation and address size faults;
    `ESR_ELx_FSC_FAULT_L(-1)` is 0x2B and `ESR_ELx_FSC_ADDRSZ_L(-1)` is 0x29,
    which the mask does not reduce to `ESR_ELx_FSC_FAULT` or
    `ESR_ELx_FSC_ADDRSZ`.
  - Safe: for permission and access flag faults, which
    `esr_fsc_is_permission_fault()` and `esr_fsc_is_access_flag_fault()`
    define for levels 0 to 3 only, as `par_check_s1_perm_fault()` in
    `arch/arm64/kvm/at.c` does.
- Same ISS bits read under two classes, for example:
  - `do_watchpoint()` in `arch/arm64/kernel/hw_breakpoint.c`: `ESR_ELx_WNR`
    under the watchpoint classes.
  - `do_fpsimd_exc()`: `ESR_ELx_FP_EXC_TFV` under `ESR_ELx_EC_FP_EXC32` and
    `ESR_ELx_EC_FP_EXC64`.
  - `arm64_ras_serror_get_severity()` in `arch/arm64/include/asm/traps.h`:
    `ESR_ELx_FSC` under SError, where 0x11 is `ESR_ELx_FSC_SERROR`; in a data
    abort the same value is `ESR_ELx_FSC_MTE`.
