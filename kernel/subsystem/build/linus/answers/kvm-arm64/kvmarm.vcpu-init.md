- Target: `kvm_vcpu_set_target()` accepts `KVM_ARM_TARGET_GENERIC_V8` or the
  value of `kvm_target_cpu()`, which is derived from the host CPU; anything
  else is `-EINVAL`.
- Unknown bits: `-ENOENT`, not `-EINVAL`; tested before host support.
- `KVM_ARM_VCPU_PMU_V3_STRICT` without `KVM_ARM_VCPU_PMU_V3`: `-EINVAL` in
  `kvm_vcpu_init_check_features()`.
- `KVM_ARM_VCPU_PMU_V3_STRICT` on a host without guest PMUv3: `-EINVAL`;
  `system_supported_vcpu_features()` drops it together with
  `KVM_ARM_VCPU_PMU_V3`.
- `KVM_ARM_VCPU_HAS_EL2_E2H0` without `ARM64_HAS_HCR_NV1`: `-EINVAL` from
  `kvm_vcpu_init_nested()`, which `kvm_setup_vcpu()` calls only when
  `vcpu_has_nv()`. `kvm_vcpu_init_check_features()` has no test for this bit.
- `kvm_setup_vcpu()` can also fail a valid feature set: `-ENODEV` from
  `kvm_arm_set_default_pmu()`, `-ENOMEM` from `kvm_vcpu_init_nested()`.
- Storage: only the VM-wide `kvm->arch.vcpu_features`; there is no per-vCPU
  feature bitmap and the target is not stored.
- Helpers: `vcpu_has_feature()` and `kvm_vcpu_has_feature()`, both
  `__vcpu_has_feature()` in `arch/arm64/include/asm/kvm_host.h`.
- `vcpu_has_sve()`: does not test the bitmap; it tests
  `KVM_ARCH_FLAG_GUEST_HAS_SVE`, which `kvm_vcpu_enable_sve()` sets during
  `kvm_reset_vcpu()`.
- `vcpu_has_nv()` and `vcpu_has_ptrauth()`: test the bitmap and a host
  capability; `vcpu_has_nv()` is constant false in code built with
  `__KVM_NVHE_HYPERVISOR__`, and `vcpu_has_ptrauth()` is constant false
  without `CONFIG_ARM64_PTR_AUTH`.
