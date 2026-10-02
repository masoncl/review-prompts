- No "IRI domain" exists: PPI, SPI and LPI each have their own parentless
  domain, kept in `gicv5_global_data`, the single `struct gicv5_chip_data`.
- `gicv5_iri_irq_mask()` and the other helpers with that prefix in
  `drivers/irqchip/irq-gic-v5.c` are code shared by the SPI and LPI chips,
  not a domain.
- hwirq in the PPI, SPI and LPI domains: the ID only, never the type.
  - The type is in the firmware specifier: DT cell 0, or bits
    `GICV5_HWIRQ_TYPE` of ACPI `param[0]`.
- Domain hierarchy, with what each level stores:

| Domain | Parent | hwirq | `chip_data` |
|---|---|---|---|
| `ppi_domain` | none | PPI ID | `NULL` |
| `spi_domain` | none | SPI ID | owning `struct gicv5_irs_chip_data` |
| `lpi_domain` | none | LPI ID | `NULL` |
| `ipi_domain` | `lpi_domain` | index in the IPI block | `NULL` |
| ITS domain, one per ITS | `lpi_domain` | EventID << 32 \| DeviceID | `struct gicv5_its_dev` |
| IWB per-device MSI domain | ITS domain | wire number | `struct gicv5_iwb_chip_data` |

- SPIs: no in-memory table; trigger mode goes through IRS MMIO in
  `gicv5_spi_irq_set_type()`, which is why an SPI's `chip_data` is its IRS.
- IRS list and CPU binding, all in `drivers/irqchip/irq-gic-v5-irs.c`:
  `irs_nodes` is the list, `per_cpu_irs_data` the CPU's IRS, `cpu_iaffid` the
  CPU's IAFFID.
- IAFFID and CPU-to-IRS binding: filled from firmware at IRS probe (DT `cpus`
  and `arm,iaffids` of the IRS node; ACPI `iaffid` and `irs_id` of the MADT
  GICC entry), not read from the CPU.
- `struct gicv5_its_chip_data`: has no link to any IRS object; the parent of
  its domain is `gicv5_global_data.lpi_domain`.
- `struct gicv5_its_dev`: `event_map` is a bitmap of EventIDs in use; the LPI
  of an event is not stored there, it is `d->parent_data->hwirq`.
- EventID-to-LPI link in the ITT: exists only between
  `gicv5_its_irq_domain_activate()` and `gicv5_its_irq_domain_deactivate()`,
  not from allocation.
- Translate frame (doorbell) address: per device, in `its_trans_phys_base` of
  `struct gicv5_its_dev`; an ITS may have several translate frames.
- DeviceID and translate frame address: resolved by `its_v5_pci_msi_prepare()`
  and `its_v5_pmsi_prepare()` in `drivers/irqchip/irq-gic-its-msi-parent.c`,
  a file shared with the GICv3 ITS.
- DT nesting: the `arm,gic-v5` node holds IRS nodes, each IRS node holds its
  ITS nodes, each ITS node holds its translate frame nodes; see
  `gicv5_irs_its_probe()`.
