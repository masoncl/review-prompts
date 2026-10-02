- `drivers/irqchip/irq-gic-its-msi-parent.c`: holds both
  `gic_v3_its_msi_parent_ops` and `gic_v5_its_msi_parent_ops`.
- ITS domain: one per `struct its_node`, an MSI parent domain made by
  `its_init_domain()` through `msi_create_parent_irq_domain()`; its parent is
  the main domain (`its_parent`).
- MSI layer above the ITS: per-device MSI domains only; there is no global
  PCI-MSI or platform-MSI domain, and no its_domain variable (only
  `its_domain_ops`).
- ITS domain `host_data`: a `struct msi_domain_info`, whose `data` is the
  `struct its_node`.
- Main domain (`gic_data.domain`): holds LPIs as well as SGI/PPI/SPI;
  `its_irq_gic_domain_alloc()` allocates each LPI in it, for device LPIs and
  for vPE doorbells.
- LPI numbers: one global space, `lpi_range_list` of `struct lpi_range`;
  device LPI blocks and vPE doorbell blocks both come from `its_lpi_alloc()`.
- `struct rdists`: holds no LPI allocation bitmap and no
  `struct redist_region`; its per-CPU part is an anonymous struct reached
  through `rdist`, there is no struct rdist_cpu.
- `struct redist_region`: array in `struct gic_chip_data`, one entry per MMIO
  region, not indexed by CPU.
- PPI partitions: there is no struct partition_desc and no partition domain;
  `struct partition_affinity` in `drivers/irqchip/irq-gic-v3.c` is a cpumask
  per DT partition node, reported by `gic_irq_get_fwspec_info()`.
- `struct its_collection`: `its->collections` is indexed by Linux CPU number,
  and `col_id` is that number once `its_cpu_init_collection()` has mapped the
  collection for that CPU; `event_map.col_map[]` and `vpe->col_idx` are both
  such indexes.
- vPE domain: one per `struct its_vm` (`vm->domain`), made in
  `its_alloc_vcpu_irqs()` directly on the main domain, not on an ITS domain;
  there is no its_vpe_domain variable, only `its_vpe_domain_ops`.
- vPE domain hwirq: the index of the vPE in the VM; the doorbell LPI
  (`vpe_db_lpi`) is the hwirq at the parent level; chip data is the
  `struct its_vpe`.
- vSGI domain: one per `struct its_vpe` (`sgi_domain`), linear, 16 interrupts,
  no parent domain; chip data is the `struct its_vpe`.
- `struct its_vm` and `struct its_vpe` storage: embedded in KVM's
  `struct vgic_dist` and `struct vgic_v3_cpu_if`; the only memory
  `vgic_v4_init()` allocates for them is the `vpes` pointer array.
- vPE tables: not part of `struct its_vm`; they belong to every v4 ITS
  (`struct its_baser` of type `GITS_BASER_TYPE_VCPU`) and, with `has_rvpeid`,
  to the redistributors; see `its_alloc_vpe_table()`.
- `struct its_vlpi_map`: the caller's object is copied into
  `event_map.vlpi_maps[]` by `its_vlpi_map()`; the array exists only while the
  device has forwarded events.
- `event_map.vm`: one `struct its_device` forwards events into one
  `struct its_vm` at a time.
- `struct its_cmd_info`: has three receivers, chosen by the irq it is sent
  on: device LPI (`its_irq_chip`), vPE doorbell, vSGI (`its_sgi_irq_chip`);
  each accepts a different subset of `enum its_vcpu_info_cmd_type`.
- KVM entry points: there is no its_vcpu_irq function; the calls are in
  `drivers/irqchip/irq-gic-v4.c`, for example `its_map_vlpi()` and
  `its_make_vpe_resident()`.
- `vpe_proxy`: file-static in `drivers/irqchip/irq-gic-v3-its.c`;
  `vpe_proxy.dev` is a `struct its_device` with no LPIs of its own, on the
  first ITS in `its_nodes`, whose events are mapped to vPE doorbells.
- `vpe_proxy` is built by `its_init_vpe_domain()` only when
  `gic_rdists->has_direct_lpi` is false; a set `has_rvpeid` keeps that flag
  true in the redistributor scan, so with `has_rvpeid` there is no proxy.
