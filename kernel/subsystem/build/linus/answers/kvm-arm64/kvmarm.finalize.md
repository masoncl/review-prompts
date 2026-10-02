- "Absent" test: `kvm_arm_vcpu_finalize()` uses `vcpu_has_sve()`, which reads
  the VM flag `KVM_ARCH_FLAG_GUEST_HAS_SVE`, not the feature bitmap.
- Check order in `kvm_arm_vcpu_finalize()`: `-EINVAL` for no SVE is tested
  before `-EPERM` for already finalised.
- Allocation and what is frozen: in `kvm_vcpu_finalize_sve()` in
  `arch/arm64/kvm/reset.c`.
