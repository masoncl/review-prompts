- Adopted path: `lpi_id_bits` is the `GICR_PROPBASER` field plus one, and is
  not clamped to `ITS_MAX_LPI_NRBITS` or to `GICD_TYPER_ID_BITS()`;
  `GICR_PROPBASER_IDBITS_MASK` is 0x1f.
- `GICD_TYPER_NUM_LPIS()`: returns the field plus one, used as an exponent;
  `its_lpi_init()` computes `numlpis = 1UL << GICD_TYPER_NUM_LPIS()`.
- `numlpis` is used when it is greater than 2 (the field is non-zero) and not
  greater than `(1UL << id_bits) - 8192`; when it is greater than that,
  `WARN_ON()` fires and the computed count stays.
- `numlpis` replaces only the count passed to `free_lpi_range()`;
  `lpi_id_bits`, the table sizes and the IDbits written to `GICR_PROPBASER`
  stay as chosen.
- Besides `lpi_id_bits` and `numlpis`, nothing in
  `its_setup_lpi_prop_table()` or `its_lpi_init()` lowers the count; there is
  no clamp by memory size.
