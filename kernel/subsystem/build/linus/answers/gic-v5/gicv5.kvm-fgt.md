- GICv5 guest: three trap bits are forced, and no others. They cover reads of
  `ICC_IDR0_EL1` and `ICC_IAFFIDR_EL1` (`__compute_ich_hfgrtr()`) and
  writes of `ICC_PPI_ENABLER0_EL1` and `ICC_PPI_ENABLER1_EL1`
  (`__compute_ich_hfgwtr()`, one bit for both registers).
- Not trapped for a GICv5 guest: the PPI pending, priority, active and
  handling-mode registers, `ICC_CR0_EL1`, `ICC_PCR_EL1`, `ICC_APR_EL1`,
  `ICC_ICSR_EL1`, `ICC_HPPIR_EL1`.
- Instructions: none trapped for a GICv5 guest; `kvm_vcpu_load_fgt()` runs
  plain `__compute_fgt()` on `ICH_HFGITR_EL2`, with no forced bits.
- Polarity: a set bit means no trap. Every GICv5 `SR_FGT()` entry in
  `arch/arm64/kvm/emulate-nested.c` has polarity 0, so a forced trap is
  `&= ~bit` after `__compute_fgt()`.
- Guest without GICv5, host with `ARM64_HAS_GICV5_CPUIF`: every trap bit of
  the three registers maps to `FEAT_GCIE` in `arch/arm64/kvm/config.c`, so all
  land in `kvm->arch.fgu[]` and `__compute_fgt()` clears them all.
- UNDEF for that guest: injected by `triage_sysreg_trap()` from
  `kvm->arch.fgu[]`, before any handler in `arch/arm64/kvm/sys_regs.c` runs.
- GICv5 handlers: make no feature test of their own; `kvm_has_gicv5()` has no
  caller under `arch/arm64`. The FGU test in `triage_sysreg_trap()` is the
  only gate.
- Host without `ARM64_HAS_GICV5_CPUIF`: `kvm_vcpu_load_fgt()` computes none
  of the three registers and `__activate_traps_ich_hfgxtr()` writes none.
