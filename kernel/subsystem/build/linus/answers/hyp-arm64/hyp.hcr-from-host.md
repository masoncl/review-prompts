- At load, `handle___pkvm_vcpu_load()`: `HCR_TWE | HCR_TWI` from the x3
  argument, protected vCPUs only.
- On each entry, `flush_hyp_vcpu()`: `HCR_TWI | HCR_TWE | HCR_VSE` from
  `READ_ONCE(host_vcpu->arch.hcr_el2)`, both kinds.
- `HCR_VI`, `HCR_VF`: not taken from the host.
- `pkvm_vcpu_reset_hcr()`: sets `HCR_FWB` with `ARM64_HAS_STAGE2_FWB`, and
  `HCR_API | HCR_APK` when `vcpu_has_ptrauth()`; `pvm_init_traps_hcr()` sets
  neither.
- `HCR_TID4` in `pkvm_vcpu_reset_hcr()`: also requires the VM's `SYS_CTR_EL0`
  value to equal `read_cpuid(CTR_EL0)`; otherwise `HCR_TID2`.
- VM `ctr_el0`: copied from the host by `pkvm_init_features_from_host()` for
  protected VMs too, so the host picks between `HCR_TID4` and `HCR_TID2`.
- **Unsafe usage**: writing host-supplied bits into a protected hyp vCPU's
  `arch.hcr_el2` outside the two masks above, by assignment, or by an OR
  without a mask.
  - Safe: clear the mask in the hyp value, then OR in the register argument
    under the same mask, as `handle___pkvm_vcpu_load()` does with
    `HCR_TWE | HCR_TWI`.
  - Safe: the same with a single `READ_ONCE()` of `host_vcpu->arch.hcr_el2`,
    as `flush_hyp_vcpu()` does with `HCR_TWI | HCR_TWE | HCR_VSE`; the bits
    set by `pvm_init_traps_hcr()` are outside both masks.
