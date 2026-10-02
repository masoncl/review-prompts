- Driver side: `its_init()` passes `its_sgi_domain_ops` to `its_init_v4()`
  when any ITS is `is_v4_1()`, inside its `has_v4 & rdists->has_vlpis`
  branch; `its_alloc_vcpu_sgis()` in `drivers/irqchip/irq-gic-v4.c` creates
  `sgi_domain` and allocates the 16 irqs only if `has_v4_1_sgi()`, which adds
  `gic_cpuif_has_vsgi()`.
- KVM side: `system_supports_direct_sgis()` is `has_gicv4_1` and
  `gic_cpuif_has_vsgi()`; `has_gicv4_1` comes from
  `gic_data.rdists.has_rvpeid` and `gicv4_enable`, and `vgic_v3_probe()`
  assigns it only when `gic_data.rdists.has_vlpis` was set.
- `GICD_TYPER2_nASSGIcap` of the host: tested by neither; in
  `drivers/irqchip/irq-gic-v3.c` it only decides whether `gic_dist_init()`
  sets `GICD_CTLR_nASSGIreq` in the host's `GICD_CTLR`.
- `find_4_1_its()`: returns this CPU's `local_4_1_its` when set; the first
  `is_v4_1()` entry of `its_nodes` is only the fallback.
- `local_4_1_its`: set in `inherit_vpe_l1_table_from_its()` and copied in
  `inherit_vpe_l1_table_from_rd()`.
- Set pending: `its_sgi_set_irqchip_state()` does a `writeq_relaxed()` of
  vPE ID and `d->hwirq` to `GITS_SGIR` through `its->sgir_base`; no command
  is queued.
- Clear pending and all configuration: VSGI commands on the same
  `find_4_1_its()`, through `its_configure_sgi()`.
- Read back: goes to the redistributor of the vPE's CPU, not to an ITS; see
  `its_sgi_get_irqchip_state()`, which returns `-ENXIO` if
  `GICR_VSGIPENDR_BUSY` never clears.
