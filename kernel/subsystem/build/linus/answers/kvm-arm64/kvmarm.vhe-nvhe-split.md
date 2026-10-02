- VHE entry points are `kvm_vcpu_load_vhe()` and `kvm_vcpu_put_vhe()` in
  `arch/arm64/kvm/hyp/vhe/switch.c`; there are no
  kvm_vcpu_load_sysregs_vhe() or kvm_vcpu_put_sysregs_vhe() here.
- Load/put on VHE, every run on nVHE, beyond the EL1, EL0 and AArch32
  sysregs:

| State | VHE at load/put | nVHE in `__kvm_vcpu_run()` |
|---|---|---|
| `VTTBR_EL2`, `VTCR_EL2` | `__load_stage2()` | `__load_stage2()`, then `__load_host_stage2()` |
| `HSTR_EL2`, `PMUSERENR_EL0`, `HCRX_EL2`, fine-grained traps, MPAM traps | `__activate_traps_common()` | `__activate_traps_common()` |
| GICv3 trap bits | `__vgic_v3_activate_traps()` from `arch/arm64/kvm/vgic/vgic-v3.c` | `__hyp_vgic_restore_state()` |

- `MDCR_EL2`: the nVHE `__activate_traps()` writes it at every entry; the
  VHE `__activate_traps()` does not write it.
- vGIC list registers: every run on both, but on VHE the host does it in
  `kvm_vgic_flush_hwstate()` and `kvm_vgic_sync_hwstate()` (see
  `can_access_vgic_from_kernel()`), outside `__kvm_vcpu_run()`.
- vGIC APRs: load/put on both, with the VMCR of a GICv3 guest restored at
  load; nVHE uses the `__vgic_v3_restore_vmcr_aprs` and
  `__vgic_v3_save_aprs` hypercalls. `__vgic_v3_save_state()` saves the VMCR
  on every run.
- `CNTHCTL_EL2` on nVHE: `__timer_enable_traps()` at every entry; under hVHE
  the EL1 physical access bits are shifted left by 10.
- Every entry on both, in addition to `HCR_EL2`, the CPTR controls and the
  return state: `POR_EL0` (with `MDSCR_EL1` in
  `__sysreg_restore_common_state()`) and the vector base.
- VHE with nested virt: `HCR_EL2` is recomputed at every entry by
  `__compute_hcr()`, not taken from `vcpu->arch.hcr_el2` alone.
- Under pKVM every guest, protected or not, runs on the hyp copy in
  `struct pkvm_hyp_vcpu`; `handle___kvm_vcpu_run()` passes the host vCPU to
  `__kvm_vcpu_run()` only when pKVM is off.
- pKVM adds load/put hypercalls: `kvm_arch_vcpu_load()` calls
  `__pkvm_vcpu_load` and `kvm_arch_vcpu_put()` calls `__pkvm_vcpu_put`.
- FP under pKVM: `kvm_hyp_handle_fpsimd()` saves the host FP state at EL2
  and `fpsimd_sve_sync()` restores it after the run; without pKVM the host
  does both.
- `__timer_enable_traps()` for a protected guest: always leaves physical
  counter access untrapped.
