- Must be final: ID registers including the edits of
  `kvm_finalize_sys_regs()`, `ctr_el0`, `kvm->arch.vcpu_features`,
  `KVM_ARCH_FLAG_MTE_ENABLED`, and the vGIC model.
- NV also needs `kvm->arch.sysreg_masks`: with `ARM64_HAS_NV3`,
  `vcpu_set_hcrx()` reads `HCR_EL2` through `vcpu_el2_e2h_is_set()`.
- `KVM_ARCH_FLAG_HAS_RAN_ONCE`: still clear on the first vCPU's call; it is
  set at the end of `kvm_arch_vcpu_run_pid_change()`.
- Lock: `kvm_calculate_traps()` takes `kvm->arch.config_lock` itself, so the
  caller must not hold it.
- `kvm_finalize_sys_regs()`, `kvm_calculate_traps()` and the flag update are
  three separate `config_lock` sections.

| Computed | Scope | By |
|---|---|---|
| bits ORed into `vcpu->arch.hcr_el2` | each vCPU's first run | `vcpu_set_hcr()` |
| trap bits in `vgic_hcr` | each vCPU's first run | `vcpu_set_ich_hcr()` |
| `vcpu->arch.hcrx_el2`, assigned | each vCPU's first run | `vcpu_set_hcrx()` |
| `kvm->arch.fgu[]` | once per VM | `compute_fgu()` |

- Not computed here: `vcpu->arch.fgt[]` (see "Fine-grained trap state") and
  the RES0/RES1 masks (see "System register finalisation").
- Repeat calls: a failure later in `kvm_arch_vcpu_run_pid_change()` leaves
  `vcpu_has_run_once()` false, so the next `KVM_RUN` calls it again.
