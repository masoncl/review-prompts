- `istsz`: the `GICV5_IRS_IST_CFGR_ISTSZ` encoding 0, 1, 2 for entries of
  4, 8, 16 bytes; it is added to the exponent, not multiplied.
- Floor: `n` is at least 5 in both functions, so the linear table and the
  level 1 table are at least `BIT(6)` = 64 bytes, the granule of
  `GICV5_IRS_IST_BASER_ADDR_MASK`.
- Ceiling: of the two IST init functions, only
  `gicv5_irs_init_ist_linear()` has a `KMALLOC_MAX_SIZE` test.
- `gicv5_irs_init_ist_two_level()`: no size check; an oversized level 1
  table shows up as `kzalloc()` failure and `-ENOMEM`.
- `BIT()` is `unsigned long`, 64 bits here: `ARM_GIC_V5` is selected only
  from `arch/arm64/Kconfig`.
- `max(5, <u32 expression>)`: builds in this tree, because `__types_ok()` in
  `include/linux/minmax.h` accepts a non-negative signed constant against
  an unsigned operand; no `max_t()` is needed.
- That `max()` compares as unsigned, so the floor does not catch a wrapped
  subtraction.
- **Potentially unsafe usage**: subtracting the level 2 bit count from
  `lpi_id_bits` in `u32` and using the result as a shift count.
  - Unsafe: when nothing before it has established that `lpi_id_bits` is
    the larger; the wrapped value passes `max()` and reaches `BIT()`.
  - Safe: in `gicv5_irs_init_ist_two_level()`, called only after
    `gicv5_irs_init_ist()` tested
    `lpi_id_bits > (10 - l2_iste_sz) + (2 * l2sz)`.
- **Potentially unsafe usage**: storing a `BIT()` result in a field narrower
  than `unsigned long`.
  - Unsafe: when the exponent can reach the field width; the value is
    truncated without warning.
  - Safe: `l2_size` (`u32`) in `struct gicv5_chip_data`, because
    `gicv5_irs_l2_sz()` returns at most `GICV5_IRS_IST_CFGR_L2SZ_64K`,
    giving at most `BIT(16)`.
