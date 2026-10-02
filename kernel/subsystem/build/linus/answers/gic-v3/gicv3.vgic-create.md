- `-EBUSY` has three sources in `kvm_vgic_create()`
  (`arch/arm64/kvm/vgic/vgic-init.c`): `kvm_trylock_all_vcpus()` fails;
  `kvm->created_vcpus != atomic_read(&kvm->online_vcpus)` (a vCPU is
  mid-creation); any vCPU has `vcpu_has_run_once()`.
- `kvm_vm_has_ran_once()` is not called by `kvm_vgic_create()`.
- `-EEXIST`: the test is `irqchip_in_kernel()`, which reads `vgic.in_kernel`,
  not `vgic_model`.
- Type validation: `kvm_vgic_create()` has none and returns no `-EINVAL`; the
  only `-ENODEV` is GICv2 without
  `kvm_vgic_global_state.can_emulate_gicv2`. It has no host check for GICv3.
- Limit field: `kvm->max_vcpus`, not a field of `kvm->arch`.
- Order: `in_kernel`, `vgic_model`, `implementation_rev` and the bases are
  written before the per-vCPU allocation, then `kvm_vgic_finalize_idregs()`
  rewrites the VM's GIC ID register fields, then the allocation loop runs.
- `vgic_allocate_private_irqs_locked()` relies on that order: it picks the
  array size with `vgic_is_v5()`, which reads `vgic_model`.
- Existing vCPUs: only `vgic_allocate_private_irqs_locked()` is called;
  `kvm_vgic_vcpu_init()` is not. No redistributor frame is registered here.
- `KVM_DEV_TYPE_ARM_VGIC_V5` is a third model: `kvm->max_vcpus` is
  `min(VGIC_V5_MAX_CPUS, kvm_vgic_global_state.max_gic_vcpus)`, the private
  array has `VGIC_V5_NR_PRIVATE_IRQS` entries, and after success
  `kvm_timer_init_vm()` is run again.
- GICv3 only, after the allocation succeeded: `vgic.nassgicap` is set from
  `system_supports_direct_sgis()`.
