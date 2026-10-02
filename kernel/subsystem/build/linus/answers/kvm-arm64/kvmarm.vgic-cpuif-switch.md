- `__vgic_v3_restore_state()`: writes `ICH_HCR_EL2` first, unconditionally,
  then the used LRs; it does not write the VMCR.
- `__vgic_v3_activate_traps()`: writes `ICH_HCR_EL2` earlier, with trap bits
  and `ICH_HCR_EL2_En` only, when `vgic_v3_cpuif_trap` is on,
  `its_vpe.its_vm` is set or `vgic_sre` is 0.
- VMCR, GICv3 guest: written at load by `__vgic_v3_restore_vmcr_aprs()`, only
  when `vgic_sre` is non-zero.
- VMCR, GICv2 guest: written by `__vgic_v3_activate_traps()` after it clears
  `ICC_SRE_EL1`, when `ICH_HCR_EL2_En` is set in `vgic_hcr`.
- VHE: `__vgic_v3_restore_state()` runs from `kvm_vgic_flush_hwstate()`; traps
  are activated at load.
- nVHE: `__hyp_vgic_restore_state()` in `arch/arm64/kvm/hyp/nvhe/switch.c`
  activates traps, then restores, on every entry.
- Saved on every exit by `__vgic_v3_save_state()`:

  | State | Condition |
  |---|---|
  | used LRs | `used_lrs` non-zero |
  | `ICH_VMCR_EL2` | always |
  | EOIcount | `ICH_HCR_EL2_LRENPIE` set in `vgic_hcr` |

- Saved only at put: the active priority registers, by
  `__vgic_v3_save_aprs()`; there is no __vgic_v3_save_vmcr_aprs().
- Protected mode: `vgic_v3_load()` and `vgic_v3_put()` skip the VMCR and APR
  calls; `kvm_arch_vcpu_load()` and `kvm_arch_vcpu_put()` make them.
