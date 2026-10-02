- Legacy support is not in `struct gic_kvm_info`: `vgic_v5_probe()` tests
  `cpus_have_final_cap(ARM64_HAS_GICV5_LEGACY)` and records it in
  `kvm_vgic_global_state.has_gcie_v3_compat`; the capability comes from
  `ICC_IDR0_EL1_GCIE_LEGACY` in `test_has_gicv5_legacy()`.
- Handoff from `drivers/irqchip/irq-gic-v5.c`: only `gicv5_of_init()` calls
  `gic_of_setup_kvm_info()`, which needs `gicv5_global_data.virt_capable`
  and a maintenance interrupt; the ACPI `gic_acpi_init()` in that file hands
  nothing to KVM.
- Host without legacy support: `vgic_v5_probe()` returns 0 if it registered
  `KVM_DEV_TYPE_ARM_VGIC_V5`, and `-ENODEV` only if it did not (pKVM, or
  registration failed).
- Host with legacy support: `vgic_v5_probe()` registers both
  `KVM_DEV_TYPE_ARM_VGIC_V5` and `KVM_DEV_TYPE_ARM_VGIC_V3`; under pKVM only
  the GICv3 one.
- `max_gic_vcpus` with legacy support: `min(VGIC_V3_MAX_CPUS,
  VGIC_V5_MAX_CPUS)`.
- `nr_lr`: taken from `vgic_ich_vtr()`; `vgic_v5_probe()` does not call
  `__vgic_v3_get_gic_config()`.
- Maintenance interrupt: set up by `kvm_vgic_hyp_init()` after the probe,
  not by `vgic_v5_probe()`.
- `vgic_host_has_gicv3()`: defined in `arch/arm64/kvm/vgic/vgic.h`; the
  per-VM test is `vgic_is_v3()`; there is no vgic_is_v3_compat() here.
- `__vgic_v3_compat_mode_enable()`: called from
  `__vgic_v3_restore_vmcr_aprs()`, so on vCPU load, not from
  `__vgic_v3_activate_traps()`.
- Clearing `ICH_VCTLR_EL2_V3`: there is no __vgic_v3_compat_mode_disable();
  nothing on the put path writes `ICH_VCTLR_EL2`, so the bit stays set after
  a GICv3 guest is put; `__vgic_v5_compat_mode_disable()` in
  `arch/arm64/kvm/hyp/vgic-v5-sr.c` clears it, called from
  `__vgic_v5_restore_vmcr_apr()` when a GICv5 guest is loaded.
- HW-mode LRs are still used: `no_hw_deactivation` is not set on a GICv5
  host, so `vgic_v3_compute_lr()` sets `ICH_LR_HW` for mapped interrupts.
- `vgic_v3_deactivate_phys()` in `arch/arm64/kvm/vgic/vgic-v3.c`: used only
  where KVM emulates the deactivation in software, in the EOIcount replay of
  `vgic_v3_fold_lr_state()` and in `vgic_v3_deactivate()`.
- With `ARM64_HAS_GICV5_LEGACY`, `vgic_v3_deactivate_phys()` issues
  `gic_insn()` CDDI instead of `gic_write_dir()`, with the type field
  hard-coded to 1, the value of `GICV5_HWIRQ_TYPE_PPI`.
