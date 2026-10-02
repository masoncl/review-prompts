- Example: `ID_AA64MMFR3_EL1` `TCRX`; search for `kvm_has_tcr2()` to see
  the trap, visibility and context-switch pieces.
- What must agree with the descriptor:
  - `struct arm64_ftr_bits` entry in `arch/arm64/kernel/cpufeature.c`:
    `init_cpu_ftr_reg()` zeroes any field without one.
  - `__kvm_read_sanitised_id_reg()` and the helpers it calls, such as
    `sanitise_id_aa64pfr0_el1()`, in `arch/arm64/kvm/sys_regs.c`: the limit.
  - `limit_nv_id_reg()` in `arch/arm64/kvm/nested.c`: the limit under NV.
  - `pvm_calc_id_reg()` and its `MAX_FEAT()` tables in
    `arch/arm64/kvm/hyp/nvhe/sys_regs.c`: protected VMs.
  - Feature maps in `arch/arm64/kvm/config.c`; see "Feature dependency
    tables".
  - `SR_FGT()` entries in `arch/arm64/kvm/emulate-nested.c`: `aggregate_fgt()`
    builds the FGT masks from them.
  - `tools/testing/selftests/kvm/arm64/set_id_regs.c`.
- Allow-list registers: `ID_AA64MMFR3_EL1`, `ID_AA64ISAR3_EL1` and
  `ID_AA64PFR2_EL1` keep only named fields, in both the limit and the
  writable mask; a new field stays hidden until added to the limit, and
  not writable until added to the mask.
- Protected VM: a register `pvm_calc_id_reg()` does not handle reads as 0, so
  a new field in such a register is hidden there by default.
- Non-protected pKVM VM: hyp tests the copy made by `vm_copy_id_regs()`, and
  takes `hcrx_el2` from the host in `pkvm_vcpu_init_traps()`.
- **Potentially unsafe usage**: adding a field to
  `arch/arm64/tools/sysreg` and `arch/arm64/kernel/cpufeature.c`.
  - Unsafe: for a register whose limit is not an allow-list, when KVM
    neither masks the field nor handles the feature; the guest sees it with
    no KVM change. `set_id_aa64pfr0_el1()` carries the MPAM clean-up for
    this.
  - Safe: for a register whose limit is an allow-list, as `ID_AA64MMFR3_EL1`
    is in `__kvm_read_sanitised_id_reg()`.
  - Safe: when the same patch masks the field in the limit, as
    `sanitise_id_aa64pfr1_el1()` does for `ID_AA64PFR1_EL1_GCS`.
- **Unsafe usage**: letting a field through the limit when the registers it
  advertises are not enabled, context switched and made to UNDEF when
  the field is lowered.
  - Safe: all keyed on one test, as for `TCRX`: `vcpu_set_hcrx()` sets
    `HCRX_EL2_TCR2En`, `tcr2_visibility()` hides `TCR2_EL1`, and
    `ctxt_has_tcrx()` gates save and restore.
