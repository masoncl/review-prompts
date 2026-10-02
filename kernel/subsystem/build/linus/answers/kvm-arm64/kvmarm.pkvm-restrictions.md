- `kvm_pkvm_ext_allowed()` has three outcomes, not two:

| Capability | Result |
|---|---|
| In the explicit list at the top of the switch | allowed for every VM |
| `KVM_CAP_ARM_MTE`, `KVM_CAP_ARM_EAGER_SPLIT_CHUNK_SIZE`, `KVM_CAP_ARM_SUPPORTED_BLOCK_SIZES` | refused for every VM |
| Anything else | allowed only if the VM is not protected, or `kvm` is NULL |

- `KVM_CAP_ARM_PMU_V3` and `KVM_CAP_ARM_SVE` are not in the explicit list, so
  both are refused for a protected VM.
- Host callers test `is_protected_kvm_enabled()` first:
  `kvm_vm_ioctl_check_extension()`, `kvm_vm_ioctl_enable_cap()`, and
  `kvm_arch_vm_ioctl()` through `kvm_pkvm_ioctl_allowed()`.
- `kvm_pkvm_ioctl_allowed()`: maps the ioctl to a capability with
  `vm_ioctl_caps[]` in `arch/arm64/kvm/arm.c` and passes it to
  `kvm_pkvm_ext_allowed()`; an ioctl missing from that table gets `-EINVAL`
  from `kvm_arch_vm_ioctl()` for every VM once pKVM is on.
- vCPU features are decided at EL2 by `pkvm_init_features_from_host()` in
  `arch/arm64/kvm/hyp/nvhe/pkvm.c`, during `__pkvm_init_vm`.
- `pkvm_init_features_from_host()` for a protected VM: allows
  `KVM_ARM_VCPU_PSCI_0_2` always, and `KVM_ARM_VCPU_PMU_V3`,
  `KVM_ARM_VCPU_PTRAUTH_ADDRESS`, `KVM_ARM_VCPU_PTRAUTH_GENERIC`,
  `KVM_ARM_VCPU_SVE` only if `kvm_pkvm_ext_allowed()` allows the matching
  capability; the result is ANDed with the host's `vcpu_features`.
- `pkvm_init_features_from_host()` for a non-protected VM: copies the host's
  `vcpu_features` unchanged.
- `KVM_ARM_VCPU_INIT` with a feature refused for a protected VM: no error on
  that account; `kvm_vcpu_init_check_features()` has no protected-VM test and
  does not call `kvm_pkvm_ext_allowed()`.
- The refused feature stays set in the host's `kvm->arch.vcpu_features` and
  is absent from the hyp VM's, from the first `KVM_RUN` on.
- `kvm_vcpu_init_check_features()` errors are unrelated to pKVM, for example
  `-ENOENT` for an unknown bit, `-EINVAL` for a feature the system lacks.
