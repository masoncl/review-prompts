- `noncoherent` argument of `gicv5_its_init_bases()`, device tree path:
  `gicv5_its_init()` passes `of_property_read_bool(node, "dma-noncoherent")`.
- `noncoherent` argument of `gicv5_its_init_bases()`, ACPI path:
  `gic_acpi_parse_madt_its()` passes
  `its_entry->flags & ACPI_MADT_GICV5_ITS_NON_COHERENT`.
- `of_dma_is_coherent()`: not called by the ITS driver.
- ACPI path, `np`: `handle` comes from `irq_domain_alloc_fwnode()`, so
  `to_of_node()` returns NULL.
- **Unsafe usage**: setting `ITS_FLAGS_NON_COHERENT` from a device tree
  property lookup in code that both probe paths reach.
  - Unsafe: on the ACPI path the node is NULL and `of_property_read_bool()`
    returns false, so the flag stays clear whatever
    `ACPI_MADT_GICV5_ITS_NON_COHERENT` says; `GICV5_ITS_CR1` gets the
    write-back, inner-shareable attributes and `gicv5_its_dcache_clean()`
    does only `dsb(ishst)`.
  - Safe: test the `noncoherent` argument, which both callers fill in, as
    `gicv5_irs_init_bases()` does for `IRS_FLAGS_NON_COHERENT`.
