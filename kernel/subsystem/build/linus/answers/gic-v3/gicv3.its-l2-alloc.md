- Barrier: `dsb(sy)` after the level-1 entry is written and flushed, in both
  `its_alloc_table_entry()` and `allocate_vpe_l2_table()`.
- Zeroing: comes from `__GFP_ZERO`, not a separate step.
- Check-then-allocate on `table[idx]`: neither function locks or rechecks;
  `its_msi_prepare()` holds `its->dev_alloc_lock` around
  `its_create_device()`.
- `allocate_vpe_l2_table()` on a flat table: returns
  `id < npg * psz / (esz * SZ_8)`, not always true.
- `allocate_vpe_l2_table()`: returns true early without
  `gic_rdists->has_rvpeid` or when the CPU has no `rd_base`.
- Redistributor geometry: read from that CPU's `GICR_VPROPBASER` at each
  call; the entry size is `esz * SZ_8` bytes.
- Device ID with a device `GITS_BASER`: bounded only by the table size in
  `its_alloc_table_entry()`; `dev_id` is not compared with `device_ids()`.
- Device ID with no device `GITS_BASER`: `its_alloc_device_table()` tests
  `ilog2(dev_id) < device_ids(its)`.
- `device_ids()`: a macro over `its->typer`, not a field;
  `its_enable_quirk_cavium_22375()` and
  `its_enable_quirk_socionext_synquacer()` rewrite `GITS_TYPER_DEVBITS`
  there.
- Level-2 pages: nothing in the file clears a level-1 entry or frees a
  level-2 page.
