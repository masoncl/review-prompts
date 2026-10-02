- Global bits: computed by `kvm_compute_ich_hcr_trap_bits()` in
  `arch/arm64/kvm/vgic/vgic-v3.c`, an alternative callback that patches the
  constant in `vgic_ich_hcr_trap_bits()`.
- `vgic_v3_probe()`: only reads the result, through
  `vgic_v3_enable_cpuif_traps()`, to enable `vgic_v3_cpuif_trap`.
- Sources:

  | Source | Bits |
  |---|---|
  | `kvm-arm.vgic_v3_group0_trap` | `ICH_HCR_EL2_TALL0` |
  | `kvm-arm.vgic_v3_group1_trap` | `ICH_HCR_EL2_TALL1` |
  | `kvm-arm.vgic_v3_common_trap` | `ICH_HCR_EL2_TC` |
  | `ARM64_WORKAROUND_CAVIUM_30115` | `ICH_HCR_EL2_TALL0`, `ICH_HCR_EL2_TALL1` |
  | `ARM64_WORKAROUND_GICv3_BROKEN_SEIS` | `ICH_HCR_EL2_TALL0`, `ICH_HCR_EL2_TALL1`, `ICH_HCR_EL2_TDIR` |
  | no `ARM64_HAS_ICH_HCR_EL2_TDIR` | `ICH_HCR_EL2_TC` |

- `dir_trap`: has no command-line parameter.
- `vgic_hcr`: the value of `vgic_ich_hcr_trap_bits()` is never stored in it;
  `compute_ich_hcr()` ORs it in at each `__vgic_v3_restore_state()`.
- Other users of `vgic_ich_hcr_trap_bits()`: `__vgic_v3_activate_traps()` and
  `vgic_v3_flush_nested()`.
- `vcpu_set_ich_hcr()`: on a host where `vgic_host_has_gicv3()` is true, ORs
  `ICH_HCR_EL2_TALL0`, `ICH_HCR_EL2_TALL1` and `ICH_HCR_EL2_TC` into
  `vgic_hcr` for a GICv2 model or no in-kernel irqchip; called from
  `kvm_calculate_traps()`.
- `vgic_v3_configure_hcr()`: assigns `vgic_hcr` from `ICH_HCR_EL2_En` on every
  flush, at the end of `vgic_flush_lr_state()`.
- `vgic_v3_configure_hcr()` with no in-kernel irqchip: returns before it
  touches `vgic_hcr`.
- `ICH_HCR_EL2_TDIR` per vCPU, set when any of:
  - the hardware lacks `ARM64_HAS_ICH_HCR_EL2_TDIR` (shadow bit only);
  - `irqs_active_outside_lrs()`;
  - `active_spis` of the VM is non-zero.
- `ICH_HCR_EL2_vSGIEOICount`: set when no SGI targets this vCPU on the
  `ap_list`, whether or not it got an LR.
