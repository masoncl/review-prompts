- Source of the flags: firmware only; no GIC ID register is read for it.
- IRS, devicetree: `dma-noncoherent` on the IRS node, read in
  `gicv5_irs_of_init()`.
- IRS, ACPI: `ACPI_MADT_IRS_NON_COHERENT` in the MADT entry flags, read in
  `gic_acpi_parse_madt_irs()`.
- Both IRS paths pass the result as the `noncoherent` argument of
  `gicv5_irs_init_bases()`, which sets `IRS_FLAGS_NON_COHERENT`.
- `gicv5_its_dcache_clean()`: static to `drivers/irqchip/irq-gic-v5-its.c`
  and takes a `struct gicv5_its_chip_data`; IRS code cannot call it.
- IRS code has no helper: each site in `drivers/irqchip/irq-gic-v5-irs.c`
  tests `IRS_FLAGS_NON_COHERENT` itself, for example
  `gicv5_irs_iste_alloc()`.
- **Potentially unsafe usage**: a store to ITS table memory that is not
  followed at once by `gicv5_its_dcache_clean()`.
  - Unsafe: when the ITS can already reach the entry, or a register write
    that makes it reachable comes before any clean.
  - Safe: a single entry through `its_write_table_entry()`, which cleans
    that entry.
  - Safe: a loop of stores to a table not yet reachable, then one
    `gicv5_its_dcache_clean()` over the whole table, as
    `gicv5_its_create_itt_two_level()` does for its level 1 table.
