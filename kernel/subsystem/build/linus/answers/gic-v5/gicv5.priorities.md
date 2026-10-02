- `GICV5_IRQ_PRI_MI`: `GICV5_IRQ_PRI_MASK & GENMASK(4, 5 - pri_bits)`, with
  `GICV5_IRQ_PRI_MASK` 0x1f; 5 bits gives 0x1f, 4 gives 0x1e, 1 gives 0x10.
- `pri_bits`: a file-static `u8` in `drivers/irqchip/irq-gic-v5.c`, default 5;
  it is not a field of `gicv5_global_data`, which holds the two inputs
  `cpuif_pri_bits` and `irs_pri_bits`.
- `pri_bits` is assigned in `gicv5_init_common()`, which both
  `gicv5_of_init()` and `gic_acpi_init()` call, as `min_not_zero()` of the
  two inputs.
- SPIs and LPIs: `gicv5_hwirq_init()` programs the priority with
  `gic_insn(cdpri, CDPRI)`, a system instruction, not an IRS MMIO write.
- `GICV5_IRS_SPI_CFGR`: `gicv5_spi_irq_set_type()` writes only the trigger
  mode `GICV5_IRS_SPI_CFGR_TM` to it, no priority.
- `gicv5_hwirq_init()`: issues `CDPRI` only, and does nothing for a type other
  than `GICV5_HWIRQ_TYPE_LPI` or `GICV5_HWIRQ_TYPE_SPI`.
- Mask equal to the interrupt priority: `gicv5_cpu_enable_interrupts()` writes
  `GICV5_IRQ_PRI_MI` to `SYS_ICC_PCR_EL1`, the value the interrupts get; that
  write is the driver's only access to `SYS_ICC_PCR_EL1`, it never compares a
  priority with the mask.
