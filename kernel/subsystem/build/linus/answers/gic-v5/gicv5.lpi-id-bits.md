- Starting value, IRS supports two levels: `GICV5_IRS_IDR2_ID_BITS`.
- Starting value, IRS does not: `max(LPI_ID_BITS_LINEAR,
  GICV5_IRS_IDR2_MIN_LPI_ID_BITS)`, then `min()` with
  `GICV5_IRS_IDR2_ID_BITS`; so it exceeds 12 when the IRS minimum does.
- Either value is then capped with `gicv5_global_data.cpuif_id_bits`, which
  `gicv5_set_cpuif_idbits()` sets to 16 or 24.
- Entry size with `GICV5_IRS_IDR2_ISTMD` set: `GICV5_IRS_IST_CFGR_ISTSZ_8`
  when the capped `lpi_id_bits` is below `GICV5_IRS_IDR2_ISTMD_SZ`, else
  `GICV5_IRS_IST_CFGR_ISTSZ_16`; without it, `GICV5_IRS_IST_CFGR_ISTSZ_4`.
- Two-level table: chosen only when the IRS supports it and
  `lpi_id_bits > (10 - istsz) + 2 * l2sz`, that is when the IDs do not fit
  in one level 2 table; see the end of `gicv5_irs_init_ist()`.
- Linear table on a two-level-capable IRS: `LPI_ID_BITS_LINEAR` is not
  applied; the bound is the level 2 bit count above.
- `gicv5_irs_l2_sz()`: returns a `GICV5_IRS_IST_CFGR_L2SZ_4K` style
  encoding (0, 1, 2), not a byte count.
- `gicv5_irs_l2_sz()` preference: the size equal to `PAGE_SIZE`, then 4K,
  then 16K; 64K is returned last without testing its support bit.
- To the allocator: `gicv5_init_lpis(BIT(lpi_id_bits))` stores `num_lpis`
  in `drivers/irqchip/irq-gic-v5.c`; `alloc_lpi()` passes `num_lpis - 1`
  to `ida_alloc_max()` and returns `-ENOSPC` while `num_lpis` is 0.
- **Unsafe usage**: giving `gicv5_init_lpis()` a count above `BIT()` of the
  value written to `GICV5_IRS_IST_CFGR_LPI_ID_BITS`.
  - Unsafe: `lpi_id_bits` is passed by value to the table init functions, so
    a value lowered there does not reach `gicv5_init_lpis()`;
    `gicv5_irs_iste_alloc()` indexes `l1ist_addr` with `lpi >> l2_bits` and
    has no bounds check.
  - Safe: the same unchanged value feeds both, as on the
    `gicv5_irs_init_ist_two_level()` path.
