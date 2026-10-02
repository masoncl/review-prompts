- Device tree: `cpus` (phandles) and `arm,iaffids` (u16 array) on the IRS
  node, paired by index; the IAFFID is not derived from the MPIDR.
- ACPI: `gic_acpi_parse_iaffid()` in `drivers/irqchip/irq-gic-v5-irs.c`;
  `gicv5_irs_acpi_init_affinity()` walks every
  `ACPI_MADT_TYPE_GENERIC_INTERRUPT` entry once per IRS.
- ACPI match: `irs_id` of `struct acpi_madt_generic_interrupt` equal to
  `irs_id` of the IRS entry; the value is its `iaffid` field.
- ACPI CPU number: `get_logical_index(gicc->arm_mpidr)`; the code does not
  call `acpi_cpu_get_madt_gicc()`.
- ACPI entries with neither `ACPI_MADT_ENABLED` nor
  `ACPI_MADT_GICC_ONLINE_CAPABLE`: skipped silently.
- `gicv5_irs_cpu_to_iaffid()` for a CPU with `valid` false: returns
  `-ENODEV`, prints an error, leaves `*iaffid` unwritten.
- `gicv5_irs_clear_affinity()`: sets `valid` false and `per_cpu_irs_data`
  NULL again for every CPU of an IRS whose probe fails after the affinity
  parse, or that `gicv5_irs_remove()` removes.
