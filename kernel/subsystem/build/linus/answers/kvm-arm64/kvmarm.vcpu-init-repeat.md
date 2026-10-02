- VM that has run: `kvm_vcpu_set_target()` and `__kvm_vcpu_set_target()` test
  neither `kvm_vm_has_ran_once()` nor `vcpu_has_run_once()`; the call is not
  refused for having run.
- Repeat on an initialised vCPU: `kvm_vcpu_set_target()` compares with
  `kvm_vcpu_init_changed()` and calls `kvm_reset_vcpu()` without
  `kvm->arch.config_lock`; `kvm_setup_vcpu()` is not run again.
- vCPU whose `VCPU_INITIALIZED` was cleared: takes the first-call path through
  `__kvm_vcpu_set_target()`, so the features must still match the VM's.
- `stage2_unmap_vm()` or `icache_inval_all_pou()`: runs only if this vCPU has
  run; init of a vCPU that never ran does neither, even on a VM that has run.
- `vcpu_reset_hcr()`: sets `hcr_el2` to `HCR_GUEST_FLAGS` only while
  `!vcpu_has_run_once()`; after a run it only ORs in `HCR_TVM` on hosts
  without `ARM64_HAS_STAGE2_FWB`.
- Repeat before SVE is finalised: `kvm_vcpu_enable_sve()` sets
  `vcpu->arch.sve_max_vl` back to `kvm_sve_max_vl`, discarding a length
  written through `KVM_REG_ARM64_SVE_VLS`.
