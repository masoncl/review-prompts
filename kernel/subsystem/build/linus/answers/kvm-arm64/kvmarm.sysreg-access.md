- `__vcpu_sys_reg(v, r)`: yields a value, not an lvalue; `__vcpu_sys_reg(v, r) = x`
  does not compile.
- `__vcpu_assign_sys_reg(v, r, val)` and `__vcpu_rmw_sys_reg(v, r, op, val)`:
  the two `__vcpu_` register accessors that write memory; `op` is for example
  `|=`.
- `SYSREGS_ON_CPU`: the vcpu flag that `locate_register()` tests; there is no
  sysregs_loaded_on_cpu field.
- `__vcpu_load_switch_sysregs()` sets the flag and
  `__vcpu_put_switch_sysregs()` clears it, in
  `arch/arm64/kvm/hyp/vhe/sysreg-sr.c`; there is no kvm_vcpu_put_sysregs_vhe().
- There is no __vcpu_read_sys_reg_from_cpu(), __vcpu_write_sys_reg_to_cpu(),
  get_el2_to_el1_mapping() or PURE_EL2_SYSREG here; `locate_register()`,
  `read_sr_from_cpu()` and `write_sr_to_cpu()` in `arch/arm64/kvm/sys_regs.c`
  do that job.
- Mapped EL2 register with a translation function and guest E2H clear
  (`SR_LOC_XLATED`): `vcpu_read_sys_reg()` returns the memory copy, with no
  reverse translation.
- `vcpu_write_sys_reg()` on a loaded register: writes the CPU (translated if
  `SR_LOC_XLATED`) and then memory (untranslated), which is what makes the
  read above correct.
- `SR_LOC_SPECIAL`: `CNTHCTL_EL2` and `CPTR_EL2`, only when `is_hyp_ctxt()` and
  guest E2H is set; otherwise `CNTHCTL_EL2` is in memory and `CPTR_EL2`
  follows the mapped rule.
- `CPTR_EL2` as `SR_LOC_SPECIAL`: read returns memory unless the host has
  `ARM64_HAS_NV2P1`; write goes to the CPU and to memory.
- `CNTHCTL_EL2` as `SR_LOC_SPECIAL`: read merges the CPU's `CNTKCTL_EL1` bits
  (`CNTKCTL_VALID_BITS`) with the memory copy unless `ARM64_HAS_NV2P1`.
- `NVHCR_EL2`: `locate_register()` puts it on the CPU when not
  `is_hyp_ctxt()` and in memory when `is_hyp_ctxt()`, the reverse of the
  mapped EL2 registers; it warns unless `kvm_has_nv3()`.
- Value read from the CPU on the `SR_LOC_LOADED` path: `vcpu_read_sys_reg()`
  masks it with `kvm_vcpu_apply_reg_masks()` when
  `reg >= __SANITISED_REG_START__`; the `SR_LOC_SPECIAL` reads from the CPU
  are not masked.
- nVHE hyp objects (`__KVM_NVHE_HYPERVISOR__`): `vcpu_read_sys_reg()` and
  `vcpu_write_sys_reg()` are macros for `__vcpu_sys_reg()` and
  `__vcpu_assign_sys_reg()`, in `arch/arm64/include/asm/kvm_emulate.h`.
- **Potentially unsafe usage**: `__vcpu_sys_reg()` or
  `__vcpu_assign_sys_reg()` on a vCPU with `SYSREGS_ON_CPU` set.
  - Unsafe: in code that wants the guest's current value, for a register
    that `vcpu_read_sys_reg()` would read from the CPU in the current context
    (`SR_LOC_LOADED` without `SR_LOC_XLATED`, `CNTHCTL_EL2` as
    `SR_LOC_SPECIAL`, or `CPTR_EL2` as `SR_LOC_SPECIAL` with
    `ARM64_HAS_NV2P1`); the read is stale and the save in
    `__vcpu_put_switch_sysregs()` overwrites the write.
  - Safe: for a register that `locate_register()` reports as
    `SR_LOC_MEMORY`, as `check_fgt_bit()` in `arch/arm64/kvm/emulate-nested.c`
    does for the guest's fine-grained trap registers.
  - Safe: in the save code itself, which stores the value it has just read
    from the CPU, as `__sysreg_save_vel2_state()` in
    `arch/arm64/kvm/hyp/vhe/sysreg-sr.c` does.
  - Safe: `vcpu_read_sys_reg()` and `vcpu_write_sys_reg()` instead, which
    call `locate_register()`, as `inject_abt64()` in
    `arch/arm64/kvm/inject_fault.c` does for ESR and FAR.
  - Safe: in the hyp switch code, for a value that code stored itself, as
    `fpsimd_lazy_switch_to_guest()` in
    `arch/arm64/kvm/hyp/include/hyp/switch.h` does for `ZCR_EL1`;
    `fpsimd_lazy_switch_to_host()` wrote the CPU value to memory at the last
    exit.
