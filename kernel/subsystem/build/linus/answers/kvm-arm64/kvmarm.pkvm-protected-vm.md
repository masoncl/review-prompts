- `pkvm_init_host_vm()` in `arch/arm64/kvm/pkvm.c` sets
  `kvm->arch.pkvm.is_protected` from `KVM_VM_TYPE_ARM_PROTECTED`; it is the
  only host writer.
- `kvm_arch_init_vm()`: returns `-EINVAL` for `KVM_VM_TYPE_ARM_PROTECTED` when
  `is_protected_kvm_enabled()` is false.
- Creating a protected VM: `pkvm_init_host_vm()` warns once and calls
  `add_taint(TAINT_USER, LOCKDEP_STILL_OK)`.
- Hypervisor's copy of the flag: taken once by `init_pkvm_hyp_vm()`, called
  from `__pkvm_init_vm()`, which runs at the first `KVM_RUN` of the VM, not at
  `KVM_CREATE_VM`.
- Every VM gets a hyp VM and hyp vCPUs once pKVM is on, protected or not; the
  host's `struct kvm_vcpu` is never run directly.
- `init_pkvm_hyp_vcpu()` copies from the host vCPU: `vcpu_id`, `vcpu_idx`,
  `arch.cflags`; when the hyp VM has `KVM_ARM_VCPU_SVE`,
  `pkvm_vcpu_init_sve()` adds `sve_max_vl` and pins the host's `sve_state`.
- Non-protected hyp vCPU: timer offsets point into the pinned host
  `struct kvm` (`arch.timer_data`); a protected one gets none.
- `__pkvm_init_vcpu` on a protected VM fails with `-EINVAL` when
  `pkvm_check_pvm_cpu_features()` rejects the hyp VM's ID registers.
- `id_regs[]` of the hyp VM: set by `pkvm_vcpu_init_sysregs()`, not by
  `pkvm_init_features_from_host()`; see "Protected guest registers and traps".
