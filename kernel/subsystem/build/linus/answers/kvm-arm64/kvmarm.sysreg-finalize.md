- It does not initialise ID registers and does not set
  `KVM_ARCH_FLAG_ID_REGS_INITIALIZED`; `kvm_reset_sys_regs()` does both.
- It does not apply `limit_nv_id_reg()`; `__kvm_read_sanitised_id_reg()`
  does.
- Steps, under `config_lock`:
  1. NV only: `kvm_init_nv_sysregs()`, before the `kvm_vm_has_ran_once()`
     test, so on every vCPU's first run.
  2. Return if `kvm_vm_has_ran_once()`.
  3. No in-kernel irqchip: clear `ID_AA64PFR0_EL1` `GIC`,
     `ID_AA64PFR2_EL1` `GCIE` and `ID_PFR1_EL1` `GIC`.
  4. In-kernel irqchip: `kvm_vgic_finalize_idregs()` sets the same three
     fields from `vgic_model`.
- `kvm_init_nv_sysregs()`, once per VM: allocates and fills
  `kvm->arch.sysreg_masks`; skipped when the pointer is set.
- `kvm_init_nv_sysregs()`, per vCPU: re-applies the masks to that vCPU's
  stored sanitised registers.
- Failure: `-ENOMEM` from the allocation fails `KVM_RUN` before any trap is
  computed.
- Steps 3 and 4 repeat for each vCPU that starts before
  `KVM_ARCH_FLAG_HAS_RAN_ONCE` is set; the edits are idempotent.
- Position: after `kvm_vgic_map_resources()`; for NV,
  `kvm_vcpu_allocate_vncr_tlb()` and `kvm_vgic_vcpu_nv_init()` run between it
  and `kvm_calculate_traps()`.
