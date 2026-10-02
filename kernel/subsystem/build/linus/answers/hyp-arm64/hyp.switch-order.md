- Entry order: `__sysreg32_restore_state()`,
  `__sysreg_restore_state_nvhe(guest_ctxt)`, `__load_stage2()`,
  `__activate_traps()`; stage 2 and traps come after the guest EL1 sysregs.
- `ARM64_WORKAROUND_SPECULATIVE_AT`, entry: `__sysreg_restore_el1_state()`
  writes the guest TCR_EL1 with `TCR_EPD0_MASK | TCR_EPD1_MASK` and skips
  SCTLR_EL1; `__activate_traps()` restores SCTLR_EL1 then TCR_EL1 after
  stage 2 is on.
- `ARM64_WORKAROUND_SPECULATIVE_AT`, exit: `__deactivate_traps()` sets the EPD
  bits, then sets `SCTLR_ELx_M`; the host's SCTLR_EL1 and TCR_EL1 come back in
  `__sysreg_restore_el1_state()`.
- `host_ctxt->__hyp_running_vcpu`: set before
  `__sysreg_save_state_nvhe(host_ctxt)`; besides `hyp_panic()`, the helpers in
  `arch/arm64/kvm/hyp/include/hyp/sysreg-sr.h` use it to pick the host branch.
- `___deactivate_traps()`: runs first in `__deactivate_traps()`; it reads
  `HCR_VSE` back from the hardware HCR_EL2 before `write_sysreg_hcr()` loads
  the host value.
- `__fpsimd_save_fpexc32()`: runs after
  `__sysreg_restore_state_nvhe(host_ctxt)`, only if `guest_owns_fp_regs()`.
- `__debug_save_host_buffers_nvhe()`: also disables BRBE and switches
  TRFCR_EL1, before the `dsb(nsh)`.
- There is no kvm_adjust_pc() here; `__kvm_adjust_pc()` runs after the
  `dsb(nsh)` and before the guest sysreg restore.
