- Function: `gicv5_irs_init_bases()`, called before any ID register is read.
- Non-coherent: `GICV5_IRS_CR1_SH` is not set; `GICV5_IRS_CR1_IC` and
  `GICV5_IRS_CR1_OC` are `GICV5_NON_CACHE`; allocation hints are the no-alloc
  values.
- `GICV5_IRS_CR1_VPET_WA` and `GICV5_IRS_CR1_VMT_WA`: set in neither branch.
- Non-coherent is selected by the presence of `dma-noncoherent` on the IRS
  node, or by `ACPI_MADT_IRS_NON_COHERENT` in `flags` of
  `struct acpi_madt_gicv5_irs`; the default is coherent.
- Flag name: `IRS_FLAGS_NON_COHERENT`, private to
  `drivers/irqchip/irq-gic-v5-irs.c`.
- `gicv5_irs_wait_for_idle()` after the `GICV5_IRS_CR0` write: its return
  value is ignored.
- `gicv5_irs_disable()`: writes 0 to `GICV5_IRS_CR0` and waits for idle.
- `gicv5_irs_disable()` callers: `gicv5_irs_remove()` for every IRS, and the
  error paths of `gicv5_irs_of_init()` and `gic_acpi_parse_madt_irs()` once
  the registers are mapped.
- All of these are `__init`; the driver has no suspend, shutdown or CPU PM
  hook that disables an IRS.
