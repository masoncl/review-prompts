- `kvm_set_vm_id_reg()` returns `void`: on a VM that has run, `KVM_BUG_ON()`
  warns once and calls `kvm_vm_bugged()`, and the value is not stored.
- The caller sees no error; later ioctls on the VM, its vCPUs and its
  devices return `-EIO`.
- Same result for an encoding `__vm_id_reg()` does not know.
- Every call site avoids the late case first: `set_id_reg()`,
  `set_imp_id_reg()` and `kvm_finalize_sys_regs()` test
  `kvm_vm_has_ran_once()`; `reset_vm_ftr_id_reg()` tests
  `KVM_ARCH_FLAG_ID_REGS_INITIALIZED`; `kvm_vgic_create()` tests
  `vcpu_has_run_once()` on each vCPU.
- Mask array: covers Op0=3, Op1 in {0, 1, 3}, CRn=0, CRm 0 to 7;
  `KVM_ARM_FEATURE_ID_RANGE_SIZE` entries.
- Index: `KVM_ARM_FEATURE_ID_RANGE_IDX()` in
  `arch/arm64/include/uapi/asm/kvm.h`; `KVM_ARM_FEATURE_ID_RANGE_INDEX()` is
  the one-argument wrapper private to `arch/arm64/kvm/sys_regs.c`.
- `kvm_vm_ioctl_get_reg_writable_masks()`: reports the static `val` of
  descriptors that have `set_user`; it consults no VM state.
- A reported bit is no promise: `MIDR_EL1`, `REVIDR_EL1` and `AIDR_EL1` are
  reported without `KVM_ARCH_FLAG_WRITABLE_IMP_ID_REGS`, and
  `arm64_check_features()` and custom setters still apply.
- `KVM_CAP_ARM_SUPPORTED_REG_MASK_RANGES`: returns `BIT(0)`, a bitmap of
  supported ranges.
