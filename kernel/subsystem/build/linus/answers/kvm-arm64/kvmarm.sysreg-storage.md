- Order of `enum vcpu_sysreg`: a plain block numbered by declaration (EL0/EL1
  registers that are not VNCR-capable, PMU, pointer auth, MTE, 32-bit, EL2
  registers without masks), then the `__SANITISED_REG_START__` block (EL2
  registers with masks), then the `__VNCR_START__` block.
- VNCR block: holds many EL1 registers (`SCTLR_EL1`, `TCR_EL1`, ...) as well as
  EL2 ones (`VTTBR_EL2`, `HCRX_EL2`, ...); it is not "the EL2 registers".
- There is no __SANITISED_REG_END__; the sanitised range runs to `NR_SYS_REGS`
  and so contains the whole VNCR block.
- `MARKER()`: defined in `arch/arm64/include/asm/kvm_asm.h`; it emits the marker
  and an `__after_` entry one lower, so the marker takes no number of its own:
  `__SANITISED_REG_START__ == SCTLR_EL2`.
- Holes: VNCR numbers follow `arch/arm64/include/asm/vncr_mapping.h`, so many
  values between `__VNCR_START__` and `NR_SYS_REGS` name no register.
- `NR_SYS_REGS`: one above the highest VNCR number, not a count of registers;
  `sys_regs[]` and `struct kvm_sysreg_masks` are sized with the holes.
- With NV: only entries at or above `__VNCR_START__` are in `vncr_array`;
  `HCR_EL2`, `SCTLR_EL2` and the other EL2 registers below it stay in
  `sys_regs[]`.
- `___ctxt_sys_reg()`: picks `vncr_array` on
  `cpus_have_final_cap(ARM64_HAS_NESTED_VIRT)` and a non-NULL `vncr_array`; it
  does not test `vcpu_has_nv()`.
- nVHE hyp objects: the `vncr_array` branch is compiled out under
  `__KVM_NVHE_HYPERVISOR__`; they always index `sys_regs[]`.
