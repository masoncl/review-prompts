- vCPU limit: `kvm->max_vcpus = min(VGIC_V5_MAX_CPUS,
  kvm_vgic_global_state.max_gic_vcpus)`; `-E2BIG` if more vCPUs are online.
- Allocation: `kvm_vgic_create()` calls `vgic_allocate_private_irqs_locked()`
  for each existing vCPU; `vgic_allocate_private_irqs()` is the wrapper
  `kvm_vgic_vcpu_init()` uses for vCPUs created later.
- GICv5 layout selection: by `vgic_is_v5(vcpu->kvm)`, not by the `type`
  argument, so `vgic_model` must be set before the allocation.
- `vgic_v5_setup_private_irq()`: `intid` is `vgic_v5_make_ppi(i)`; SW_PPI is
  edge, every other PPI level; installs `vgic_v5_ppi_irq_ops`.
- `kvm_vgic_finalize_idregs()`: clears `ID_AA64PFR0_EL1.GIC`,
  `ID_AA64PFR2_EL1.GCIE` and `ID_PFR1_EL1.GIC`, then sets GCIE to IMP for
  `KVM_DEV_TYPE_ARM_VGIC_V5`.
- Second call: `kvm_finalize_sys_regs()` calls `kvm_vgic_finalize_idregs()`
  again before the first vCPU run.
