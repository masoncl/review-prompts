- Unclaimed SPI: `gicv5_irq_spi_domain_alloc()` passes the NULL from
  `gicv5_irs_lookup_by_spi_id()` to `irq_domain_set_info()` untested and
  returns 0.
- Lifetime of a non-NULL pointer: `struct gicv5_irs_chip_data` is freed only
  in `__init` code (`gicv5_irs_remove()` and the per-IRS probe error paths),
  so no reference or lock is needed to keep it alive.
- Chip data of the descriptor: reset by `irq_domain_reset_irq_data()` in
  `gicv5_irq_domain_free()`.
- There is no gicv5_irs_spi_set_type() here; `gicv5_spi_irq_set_type()` in
  `drivers/irqchip/irq-gic-v5-irs.c` reads `d->chip_data`.
- PPI, LPI and IPI: chip data is NULL; only the SPI domain stores an IRS.
- **Unsafe usage**: dereferencing the chip data of an SPI as
  `struct gicv5_irs_chip_data *` when nothing has shown that an IRS claims
  the SPI.
  - Unsafe: for an SPI ID outside every IRS range the pointer is NULL.
  - Safe: callbacks that address the SPI by `d->hwirq` alone and never read
    chip data, as `gicv5_spi_irq_set_affinity()` does.
