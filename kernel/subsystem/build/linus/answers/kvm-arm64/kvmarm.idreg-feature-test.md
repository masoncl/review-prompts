- Before the first `kvm_reset_sys_regs()`: `id_regs[]` is zero, so an
  unsigned field tests absent and a signed field whose limit is 0 tests
  present, for example `ID_AA64PFR0_EL1` `FP` against `IMP`.
- Features enabled by a vCPU feature bit or VM flag have their own test:
  `vcpu_has_nv()`, `vcpu_has_sve()`, `vcpu_has_ptrauth()`, `kvm_has_mte()`.
- `ID_AA64PFR0_EL1` `EL2`: `sanitise_id_aa64pfr0_el1()` does not clear it,
  so `kvm_has_feat()` on it can be true for a VM without NV.
- `kvm_has_fpmr()` and `kvm_has_s1poe()`: also test the host, with
  `system_supports_fpmr()` and `system_supports_poe()`.
- Host capability test: `kvm_has_feat()` makes none. Host code touches
  hardware on the guest test alone, as `__kvm_at_s1e01_fast()` does for
  `TCR2_EL1`; `arm64_check_features()` accepts a field only if it equals the
  limit or is the safe value against it.
- Hyp save and restore helpers test the host capability first, as
  `ctxt_has_tcrx()` does with `ARM64_HAS_TCR2`; under pKVM
  `vm_copy_id_regs()` copies the host's values unchecked.
- Fields KVM sets itself are not bounded by the host, for example CSV2,
  CSV3 and GIC in `sanitise_id_aa64pfr0_el1()`, and the fields
  `limit_nv_id_reg()` forces.
- **Potentially unsafe usage**: storing a decision taken from
  `kvm_has_feat()` in VM or vCPU state.
  - Unsafe: stored at vCPU create, init or reset time, when `set_id_reg()`
    still accepts another value and `kvm_finalize_sys_regs()` has not yet
    edited the GIC fields.
  - Safe: stored from `kvm_calculate_traps()`, which
    `kvm_arch_vcpu_run_pid_change()` calls after `kvm_finalize_sys_regs()`,
    as `vcpu_set_hcrx()` is; `set_id_reg()` refuses a change only once
    `KVM_ARCH_FLAG_HAS_RAN_ONCE` is set, at the end of that function.
  - Safe: not stored but tested at each use, as `tcr2_visibility()` does.
  - Safe: at hyp vCPU init for a protected VM, as `pvm_init_traps_hcr()`
    does; it reads the hyp copy, which `pkvm_vcpu_init_sysregs()` filled
    just before and `set_id_reg()` never writes.
