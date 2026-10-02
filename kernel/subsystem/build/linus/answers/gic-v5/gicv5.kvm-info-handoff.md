- `struct gic_kvm_info` has no `has_gcie_v3_compat` field;
  `gic_of_setup_kvm_info()` sets only `type`, `no_maint_irq_mask` and
  `maint_irq`.
- `has_gcie_v3_compat`: exists only in `struct vgic_global`; `vgic_v5_probe()`
  sets it from `cpus_have_final_cap(ARM64_HAS_GICV5_LEGACY)`.
- `vgic_v5_probe()`: never reads its `info` argument.
- `gic_of_setup_kvm_info()` publishes nothing when any of these holds:
  - `CONFIG_KVM` is off (empty stub);
  - `gicv5_global_data.virt_capable` is false; `gicv5_irs_init()` sets it from
    `GICV5_IRS_IDR0_VIRT` of the first IRS;
  - `irq_of_parse_and_map(node, 0)` returns 0;
  - `gicv5_irs_of_probe()` or `gicv5_init_common()` failed, so
    `gicv5_of_init()` never reaches the call.
- ACPI: `gic_acpi_init()` in `drivers/irqchip/irq-gic-v5.c` does not call
  `vgic_set_kvm_info()`, and no other code publishes `GIC_V5`.
- ACPI-booted GICv5 host: `kvm_vgic_hyp_init()` returns `-ENODEV`;
  `init_subsystems()` treats that as "no vgic" and continues, except under
  pKVM, where KVM init fails.
