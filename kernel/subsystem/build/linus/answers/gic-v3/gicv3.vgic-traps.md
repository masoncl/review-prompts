- Group enables in the VMCR do not select any trap bit.

| Condition | Bits | Held in |
|---|---|---|
| `ARM64_WORKAROUND_CAVIUM_30115` | `ICH_HCR_EL2_TALL0`, `ICH_HCR_EL2_TALL1` | patched constant |
| `ARM64_WORKAROUND_GICv3_BROKEN_SEIS` | `ICH_HCR_EL2_TALL0`, `ICH_HCR_EL2_TALL1`, `ICH_HCR_EL2_TDIR` | patched constant |
| no `ARM64_HAS_ICH_HCR_EL2_TDIR` | `ICH_HCR_EL2_TC` | patched constant |
| `kvm-arm.vgic_v3_group0_trap`, `kvm-arm.vgic_v3_group1_trap`, `kvm-arm.vgic_v3_common_trap` | the matching bit | patched constant |
| no in-kernel irqchip | `ICH_HCR_EL2_TALL0`, `ICH_HCR_EL2_TALL1`, `ICH_HCR_EL2_TC` | `vgic_hcr`, by `vcpu_set_ich_hcr()` |
| no `ARM64_HAS_ICH_HCR_EL2_TDIR`, or `irqs_active_outside_lrs()`, or `active_spis` non-zero | `ICH_HCR_EL2_TDIR` | `vgic_hcr`, by `vgic_v3_configure_hcr()` |

- `dir_trap`: has no early parameter; only the broken-SEIS case sets it.
- Patched constant: `kvm_compute_ich_hcr_trap_bits()` is the `ALTERNATIVE_CB()`
  callback of `vgic_ich_hcr_trap_bits()` in `arch/arm64/kvm/vgic/vgic.h`; the
  value is never stored in `vgic_hcr`.
- `vgic_v3_probe()`: computes no trap bits; it calls
  `vgic_v3_enable_cpuif_traps()`, which enables `vgic_v3_cpuif_trap` when the
  constant is non-zero. There is no vgic_v3_enable() here.
- `vcpu_set_ich_hcr()`: called only from `kvm_calculate_traps()`, which
  `kvm_arch_vcpu_run_pid_change()` runs before the vCPU's first run.
- `vgic_v3_configure_hcr()`: assigns `vgic_hcr` from `ICH_HCR_EL2_En` at every
  flush when `irqchip_in_kernel()`; bits ORed in elsewhere do not survive it.
- `__vgic_v3_restore_state()`: writes `compute_ich_hcr()`, which is `vgic_hcr`
  ORed with the constant, to `ICH_HCR_EL2` at every entry, with or without the
  static key.
- `__vgic_v3_activate_traps()`: writes the constant ORed with
  `ICH_HCR_EL2_En`, not `vgic_hcr`, and only if `vgic_v3_cpuif_trap` is on,
  `its_vpe.its_vm` is set or `vgic_sre` is clear.
- `vgic_hcr` without `ICH_HCR_EL2_En` (no vgic): `__vgic_v3_activate_traps()`
  sets `ICC_SRE_EL1.SRE` so that the trap bits take effect.
- `__vgic_v3_save_state()`: writes 0 to `ICH_HCR_EL2` at every exit.
- `vgic_v3_cpuif_trap`: gates only the hyp handler in
  `arch/arm64/kvm/hyp/include/hyp/switch.h` and the `ICH_HCR_EL2` writes in
  `__vgic_v3_activate_traps()` and `__vgic_v3_deactivate_traps()`; per-vCPU
  bits in `vgic_hcr` do not enable it.
- Key off: every trapped access exits to `arch/arm64/kvm/sys_regs.c`; there
  `ICC_DIR_EL1` goes to `access_gic_dir()`, and the group and common
  registers are `undef_access`.
- `access_gic_dir()`: calls `vgic_v3_deactivate()` for a write when
  `kvm_has_gicv3()`; with the key off it handles the trap that
  `ICH_HCR_EL2_TDIR` in `vgic_hcr` causes.
- `__vgic_v3_perform_cpuif_access()`: returns 0 or 1 only; it never returns
  -1 and never injects an exception itself.
- `__vgic_v3_perform_cpuif_access()`: returns 0 at once unless `vgic_model`
  is `KVM_DEV_TYPE_ARM_VGIC_V3`.
- Nested guest: `__vgic_v3_perform_cpuif_access()` returns 0 to the host when
  `__vgic_v3_check_trap_forwarding()` finds that the L1 `ICH_HCR_EL2` or, for
  `ICC_IGRPEN0_EL1` and `ICC_IGRPEN1_EL1`, the L1 `HFGRTR_EL2`/`HFGWTR_EL2`
  asks for the trap.
