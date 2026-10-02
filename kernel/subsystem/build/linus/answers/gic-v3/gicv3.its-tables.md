- Page size: `its_probe_baser_psz()` settles it before the table is
  allocated, by changing only the page-size field of the register and
  reading it back, 64K then 16K then 4K; the result is `baser->psz`.
- Page size failure: `its_probe_baser_psz()` returns -1 after 4K;
  `its_alloc_tables()` frees the earlier tables and returns `-ENXIO`.
- `its_setup_baser()`: has no page-size retry; a page-size mismatch there
  ends in the "doesn't stick" `-ENXIO`.
- Shareability mismatch: sets no per-table flag; later code tests
  `GITS_BASER_SHAREABILITY_MASK` in `baser->val`.
- Attributes carry over: the cacheability and shareability that stuck on one
  `GITS_BASER` are the start values for the next.
- Flat or two-level: `its_parse_indirect_baser()` runs for
  `GITS_BASER_TYPE_DEVICE` and `GITS_BASER_TYPE_VCPU` only; other types are
  flat.
- Two-level needs both: `(esz << ids) > psz * 2`, and `GITS_BASER_INDIRECT`
  reading back set.
- Size caps: `MAX_PAGE_ORDER` in `its_parse_indirect_baser()` and
  `GITS_BASER_PAGES_MAX` in `its_setup_baser()`; there is no
  ITS_MAX_ALLOC_ORDER.
- `MAX_PAGE_ORDER` clamp: lowers the order returned through `*order`; the
  reduced `ids` is only a local that is printed in a warning and is not
  stored.
- PA above 48 bits: tested only under
  `IS_ENABLED(CONFIG_ARM64_64K_PAGES)`.
- PA above 48 bits with `psz` not `SZ_64K`: pages freed, `-ENXIO`, no retry.
- Level-1 entries: hold the raw `page_to_phys()` with `GITS_BASER_VALID`,
  not the folded form; in `drivers/irqchip/irq-gic-v3-its.c`
  `GITS_BASER_ADDR_48_to_52()` is used only by
  `inherit_vpe_l1_table_from_its()`.
