- `*hwirq` from `gicv5_irq_domain_translate()`: the bare ID in both the device
  tree and the ACPI case, never a typed ID.
- Wanted type: only `GICV5_HWIRQ_TYPE_PPI` and `GICV5_HWIRQ_TYPE_SPI` have a
  translate wrapper; an LPI specifier matches neither domain.
- ACPI fwnode (`is_fwnode_irqchip()`): `param_count` must be exactly 2;
  `param[0]` is a typed ID split with `GICV5_HWIRQ_TYPE` and
  `GICV5_HWIRQ_ID`; `param[1]` is the trigger. `acpi_register_gsi()` in
  `drivers/acpi/irq.c` builds it from the GSI.
- ACPI GSI with `GICV5_GSI_IC_TYPE` equal to `GICV5_GSI_IWB_TYPE`:
  `gic_v5_get_gsi_domain_id()` returns the IWB fwnode, so the fwspec never
  reaches the PPI or SPI domain.
- PPI trigger: `IRQ_TYPE_LEVEL_LOW` when the HMR bit is set, else
  `IRQ_TYPE_EDGE_RISING`; the HMR is read on the CPU that runs the translate.
- `gicv5_irq_ppi_domain_select()` and `gicv5_irq_spi_domain_select()`: ignore
  the `bus_token` argument; they match on fwnode and type only.
- `irq_find_matching_fwspec()`: calls `select` only when the token is not
  `DOMAIN_BUS_ANY`; with `DOMAIN_BUS_ANY` it compares fwnodes and returns the
  first domain on the list with the GIC fwnode, whatever the type.
- `fwspec_to_domain()`: asks with `DOMAIN_BUS_WIRED` first, so wired lookups
  go through `select`; `DOMAIN_BUS_ANY` is the fallback.
- `gicv5_iwb_irq_domain_translate()`: for an ACPI device node the wire is
  `GICV5_GSI_IWB_WIRE` of `param[0]`; for device tree it is `param[0]` as is.
