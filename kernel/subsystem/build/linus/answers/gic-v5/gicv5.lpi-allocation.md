- `alloc_lpi()` with no IST set up: `num_lpis` is 0, returns `-ENOSPC`.
- `num_lpis`: `BIT(lpi_id_bits)`, set by `gicv5_irs_init_ist()`. See there for
  the bit count; the part that is easy to miss is the final cap by
  `gicv5_global_data.cpuif_id_bits`, read from the boot CPU.
- Two-level support of the IRS: the bit `GICV5_IRS_IDR2_IST_LEVELS`, tested in
  `gicv5_irs_init_ist()`; it selects the starting bit count, see "LPI ID bits
  and layout".
- `lpi_ida`: one allocator for the IPIs and for every ITS.
- `alloc_lpi()` and `release_lpi()`: static, called only by the LPI domain
  callbacks. There is no gicv5_alloc_lpi() or gicv5_free_lpi() here.
- `gicv5_lpi_config_reset()`: sets handling mode to edge and clears pending;
  it does not touch enable, priority, affinity or active state.
- `gicv5_hwirq_init()`: writes priority only (`GIC CDPRI`); nothing in
  `gicv5_irq_lpi_domain_alloc()` writes a route for the new LPI.
