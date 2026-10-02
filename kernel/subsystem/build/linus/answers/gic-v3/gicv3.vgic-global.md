- `struct gic_kvm_info`: there is no gicv_base field; the GICV region is
  `vcpu` (a `struct resource`), and `type` can also be `GIC_V5`.
- `vgic_set_kvm_info()`: allocates a private copy and `BUG_ON()`s on a
  second call; if the allocation fails the pointer stays NULL and
  `kvm_vgic_hyp_init()` later returns `-ENODEV`.
- GICv3 driver precondition: `gic_of_setup_kvm_info()` and
  `gic_acpi_setup_kvm_info()` in `drivers/irqchip/irq-gic-v3.c` run only
  while `supports_deactivate_key` is enabled; `gic_init_bases()` disables it
  when `!is_hyp_mode_available()`.
- ACPI mismatch: if the maintenance interrupt, its trigger mode or the GICV
  base differ between GICC entries, `gic_acpi_parse_virt_madt_gicc()` returns
  `-EINVAL` and nothing is handed to KVM at all.
- Missing maintenance interrupt: `kvm_vgic_hyp_init()` returns `-ENXIO` only
  when `no_maint_irq_mask` is clear; the GICv3 driver never gets that far, it
  returns before `vgic_set_kvm_info()`, so KVM sees `-ENODEV`.
- `-ENODEV` or `-ENXIO` from `kvm_vgic_hyp_init()`: `init_subsystems()` in
  `arch/arm64/kvm/arm.c` continues with `vgic_present` false (userspace
  irqchip only); it fails instead under `is_protected_kvm_enabled()`, and
  with `-EINVAL` when `kvm_mode` is `KVM_MODE_NV`.
- `vgic_v3_probe()`: has no SRE check and no `-ENODEV` return; its only
  errors come from `kvm_register_vgic_device()`.
- `__vgic_v3_get_gic_config()`: returns a bool, true if the CPU interface
  can do GICv2 MMIO; it does not return `ICH_VTR_EL2`.
- `ICH_VTR_EL2` value: comes from `vgic_ich_vtr()` in
  `arch/arm64/kvm/vgic/vgic.h`, a constant patched in by
  `kvm_patch_ich_vtr_el2()`, which also clears `ICH_VTR_EL2_SEIS` on broken
  SEIS hardware; `kvm_vgic_global_state` holds no copy of the register.
- `no_hw_deactivation`: handled in `kvm_vgic_hyp_init()` before the probe
  switch (taint, then `kvm_vgic_global_state.no_hw_deactivation`), not in
  `vgic_v3_probe()`.
- GICv2 emulation on a GICv3 host: see the if-chain in `vgic_v3_probe()`;
  the easy-to-miss cases are a GICV base that is not page aligned and
  `KVM_MODE_PROTECTED`, which both leave `can_emulate_gicv2` false while
  `KVM_DEV_TYPE_ARM_VGIC_V3` is still registered.
- `kvm-arm.vgic_v4_enable`: defaults to off (`gicv4_enable` in
  `arch/arm64/kvm/vgic/vgic-v3.c`); without it `has_gicv4` and `has_gicv4_1`
  stay false on GICv4 hardware and the log says "GICv4 support disabled".
- `has_gicv4` and `has_gicv4_1`: `vgic_v3_probe()` assigns them only inside
  `if (info->has_v4)`; `has_gicv4_1` is `info->has_v4_1 && gicv4_enable`.
