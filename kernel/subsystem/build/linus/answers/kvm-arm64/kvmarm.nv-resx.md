- Sanitised range: every `enum vcpu_sysreg` entry from
  `__SANITISED_REG_START__` to `NR_SYS_REGS`. It is not only VNCR-backed
  registers.
- Non-VNCR entries in the range: `SCTLR_EL2`, `TCR2_EL2`, `SCTLR2_EL2`,
  `MDCR_EL2`, `CNTHCTL_EL2`, `ZCR_EL2`, `HCR_EL2`.
- `TCR_EL2`, `CPTR_EL2`, `SPSR_EL2`: before the marker, never masked.
- Non-zero masks exist only for registers with a `set_sysreg_masks()` call
  in `kvm_init_nv_sysregs()`; every other register in range passes
  unchanged, for example `TCR2_EL1`.
- `NVHCR_EL2`: gets a zero mask unless `kvm_has_nv3()`.
- `ICH_HFGRTR_EL2`, `ICH_HFGWTR_EL2`, `ICH_HFGITR_EL2`: have feature maps
  in `arch/arm64/kvm/config.c` but no `set_sysreg_masks()` call.
- `__vcpu_sys_reg()`: applies the masks on read.
- `__vcpu_assign_sys_reg()` and `__vcpu_rmw_sys_reg()`: apply them on
  write.
- All three test `vcpu_has_nv()` and `r >= __SANITISED_REG_START__` first.
- `vcpu_read_sys_reg()` and `vcpu_write_sys_reg()`: also mask the value
  read from or written to the CPU register when `locate_register()`
  reports `SR_LOC_LOADED`.
- `ctxt_sys_reg()` and `__ctxt_sys_reg()`: raw, no masks.
- Stored values are not guaranteed sanitised: the guest hypervisor writes
  the VNCR page directly, and hyp save code stores through
  `ctxt_sys_reg()`. A read through `__vcpu_sys_reg()` is masked whatever
  was stored.
- `struct kvm_sysreg_masks`: an array `mask[]` of `struct resx`, indexed by
  `sr - __SANITISED_REG_START__`.
- `kvm->arch.sysreg_masks`: NULL until the first `kvm_init_nv_sysregs()`
  call, and always NULL for a VM without NV; `__kvm_get_sysreg_resx()` then
  returns zero masks.
- `get_reg_fixed_bits()`: returns `struct resx` by value;
  `set_sysreg_masks()` takes one.
- `kvm_get_sysreg_resx()`: the lookup. `kvm_get_sysreg_res0()` is a static
  wrapper in `arch/arm64/kvm/emulate-nested.c`.
