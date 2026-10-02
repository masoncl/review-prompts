- LPI domain: created by `gicv5_init_lpi_domain()` from `gicv5_irs_init()`
  for the first IRS, not by `gicv5_init_domains()`; freed by
  `gicv5_free_lpi_domain()` in `gicv5_irs_remove()`.
- `gicv5_init_domains()`: creates the PPI domain, the SPI domain only when
  `global_spi_count` is non-zero, and the IPI domain as a child of
  `gicv5_global_data.lpi_domain`; `gicv5_free_domains()` removes those three.
- Last possible failure in `gicv5_init_common()`: `gicv5_irs_enable()`.
  `gicv5_smp_init()` and `gicv5_irs_its_probe()` return void, so the hotplug
  state, the IPIs and the ITSs are never unwound.
- `gicv5_irs_enable()` failure: the `out_handle` label calls
  `set_handle_irq(NULL)`; `set_handle_irq()` in `arch/arm64/kernel/irq.c`
  returns `-EBUSY` and changes nothing once a handler is installed.
- `gicv5_irs_remove()`, left to both callers: per IRS it also calls
  `gicv5_irs_clear_affinity()` and `gicv5_irs_disable()` before unmapping.
- ITS probing: `gicv5_irs_its_probe()` inside `gicv5_init_common()` on both
  paths; it picks `gicv5_its_of_probe()` or `gicv5_its_acpi_probe()` by
  `acpi_disabled`.

| | `gicv5_of_init()` | `gic_acpi_init()` |
|---|---|---|
| entered | once, for the `arm,gic-v5` node | once per MADT IRS entry of version `ACPI_MADT_GIC_VERSION_V5`; returns 0 at once when `gsi_domain_handle` is set |
| domain fwnode | `of_fwnode_handle()` of the node | `irq_domain_alloc_fwnode(&irs->config_base_address)` |
| an IRS fails to probe | `gicv5_irs_of_probe()` logs and tries the next child | non-zero return from `gic_acpi_parse_madt_irs()` ends the walk in `acpi_parse_entries_array()`; `gicv5_irs_acpi_probe()` ignores that and tests only `list_empty(&irs_nodes)` |
| affinity parse | can fail the IRS | `gicv5_irs_acpi_init_affinity()` always returns 0 |
| `fwnode` in `struct gicv5_irs_chip_data` | the IRS node | left NULL |
| KVM | `gic_of_setup_kvm_info()` | no call to `vgic_set_kvm_info()` |
| after success | nothing more | `acpi_set_irq_model()` with `ACPI_IRQ_MODEL_GIC_V5` |
