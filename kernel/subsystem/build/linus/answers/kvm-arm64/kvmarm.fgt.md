- `kvm->arch.fgu[]`: one `u64` per `enum fgt_group_id`; a read/write
  register pair shares the group.
- `vcpu->arch.fgt[]`: same index, with separate `.r` and `.w` members.
- `vcpu_fgt()`: takes a register name from `enum vcpu_sysreg`, and picks the
  group and member.
- `fgu[]` is computed without `ARM64_HAS_FGT`, but consulted only with it:
  `populate_nv_trap_config()` stores the FGT group of an encoding only when
  the host has the cap, and `triage_sysreg_trap()` tests `fgu[]` only for an
  encoding that has a group.
- With `ARM64_HAS_FGT`: `triage_sysreg_trap()` injects UNDEF for any trapped
  access whose bit is set, whatever caused the trap.
- `ICH_HFGRTR_GROUP` and `ICH_HFGITR_GROUP`: GICv5 groups; their `fgt[]`
  values are computed in `kvm_vcpu_load_fgt()` only with `ARM64_HAS_FGT` and
  `ARM64_HAS_GICV5_CPUIF`, and written by `__activate_traps_ich_hfgxtr()`
  only with `ARM64_HAS_GICV5_CPUIF`.

| Mode | FGT registers written | By |
|---|---|---|
| VHE | at vCPU load | `kvm_vcpu_load_vhe()` |
| nVHE | on every guest entry | `__activate_traps()` in `arch/arm64/kvm/hyp/nvhe/switch.c` |

- Both reach `__activate_traps_hfgxtr()` through
  `__activate_traps_common()`.
- VHE: `kvm_arch_vcpu_load()` calls `kvm_vcpu_load_fgt()` before
  `kvm_vcpu_load_vhe()`, so a change to an input of `fgt[]` reaches hardware
  only at the next load.
- `HAFGRTR_EL2`: written only when `cpu_has_amu()`.
- Nested guest: `__compute_fgt()` merges L1's register when
  `is_nested_ctxt()`; `kvm_emulate_nested_eret()` and `kvm_inject_nested()`
  do a put and load around the context change.
- pKVM non-protected VM: `handle___pkvm_vcpu_load()` copies the host
  vCPU's `fgt[]` into the hyp vCPU.
