| Domain | Created in | Parent | fwnode | Bus token |
|---|---|---|---|---|
| PPI | `gicv5_init_domains()` | none | GIC | `DOMAIN_BUS_WIRED` |
| SPI | `gicv5_init_domains()` | none | GIC | `DOMAIN_BUS_WIRED` |
| LPI | `gicv5_init_lpi_domain()` | none | `NULL` | none |
| IPI | `gicv5_init_domains()` | LPI | `NULL` | none |
| ITS | `gicv5_its_init_domain()` | LPI | ITS | `DOMAIN_BUS_NEXUS` |
| IWB | `gicv5_iwb_create_device_domain()` | ITS | IWB device | `DOMAIN_BUS_WIRED_TO_MSI` |

- `gicv5_init_lpi_domain()`: creates the LPI domain only; called from
  `gicv5_irs_init()` for the first IRS, so before `gicv5_init_domains()` and
  before the IST exists (`gicv5_irs_enable()` runs later).
- PPI and SPI domains: `irq_domain_create_linear()`, with no parent.
- LPI and IPI domains: no fwnode and no token, so no fwnode lookup finds them;
  code reaches them through `gicv5_global_data`.
- `gicv5_init_lpi_domain()`: does not check the result of
  `irq_domain_create_tree()`; with no LPI domain `gicv5_init_domains()` warns,
  creates no IPI domain and still returns 0.
- `gicv5_free_domains()`: removes PPI, SPI and IPI domains, not the LPI
  domain; `gicv5_free_lpi_domain()`, called from `gicv5_irs_remove()`, does.
- ACPI: the PPI and SPI fwnode is `gsi_domain_handle`, allocated in
  `gic_acpi_init()`.
- ITS domain: created with `IRQ_DOMAIN_FLAG_FWNODE_PARENT`, so
  `msi_lib_irq_domain_select()` compares the parent of the looked-up fwnode
  with the ITS fwnode.
