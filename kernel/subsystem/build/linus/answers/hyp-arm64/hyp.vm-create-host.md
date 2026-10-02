- `pkvm_create_hyp_vm()` in `arch/arm64/kvm/pkvm.c`: takes `kvm->slots_lock`,
  then `kvm->arch.config_lock`; the caller already holds `vcpu->mutex`.
- Skip test: `pkvm_hyp_vm_is_created()`, which reads
  `kvm->arch.pkvm.is_created`; `kvm->arch.pkvm.handle` is already set by
  `pkvm_init_host_vm()` at VM creation.
- `kvm->slots_lock`: `kvm_arch_prepare_memory_region()` in
  `arch/arm64/kvm/mmu.c` reads `is_created` under it and returns `-EPERM`
  for `KVM_MR_DELETE` or `KVM_MR_MOVE` on a protected VM that is created.
