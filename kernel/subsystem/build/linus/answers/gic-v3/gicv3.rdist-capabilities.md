- `has_direct_lpi`: a redistributor keeps it set with any one of
  `GICR_TYPER_DirectLPIS`, `GICR_CTLR_IR`, or the running `has_rvpeid`.
- Redistributor with `GICR_TYPER_RVPEID` but without `GICR_TYPER_VLPIS`,
  while the running `has_rvpeid` is still set: `WARN_ON_ONCE()`, then
  `has_direct_lpi`, `has_vlpis` and `has_rvpeid` are cleared.
- `gic_nvidia_t241_erratum` enabled: `gic_init_bases()` never sets the four
  flags, so all stay false, `has_direct_lpi` included.
- No quirk and no command-line option clears a flag after the scan; there is
  no irqchip.gicv4_enable parameter.
- `its_init()` runs only when `gic_dist_supports_lpis()`; otherwise the flags
  stay as the redistributor scan left them.
- `its_init()` clears `has_vlpis` when no ITS was probed (returns -ENXIO),
  and when `its_init_vpe_domain()` or `its_init_v4()` fails.
- `its_init()` clears `has_rvpeid`, with `WARN_ON()`, when it is set and no
  ITS is `is_v4_1()`.
- `its_init()` with ITSs present but none `is_v4()`: leaves `has_vlpis` set.
- `its_cpu_init_lpis()`: clears `has_rvpeid` and `has_vlpis` when
  `allocate_vpe_l1_table()` fails; it runs on each CPU's first
  `its_cpu_init()`, so also on a secondary CPU long after boot.
- KVM's `has_v4` and `has_v4_1` in `struct gic_kvm_info`: copied once, in
  `gic_of_setup_kvm_info()` or `gic_acpi_setup_kvm_info()`, after
  `gic_init_bases()` returned; a later clear does not reach KVM.
- Code in `drivers/irqchip/irq-gic-v3-its.c` tests the flag in `gic_rdists`
  at the time of use, and `is_v4()` or `is_v4_1()` on the `struct its_node`
  for what is done through one ITS, for example
  `its_irq_set_vcpu_affinity()` and `its_build_vmapp_cmd()`.
- KVM code tests `kvm_vgic_global_state.has_gicv4` and `has_gicv4_1`, or
  `vgic_supports_direct_msis()` and `system_supports_direct_sgis()` in
  `arch/arm64/kvm/vgic/vgic-mmio-v3.c`.
- `gic_rdists_supports_plpis()`: tests `GICR_TYPER_PLPIS` of the local
  redistributor (physical LPIs); it is not a GICv4 test.
