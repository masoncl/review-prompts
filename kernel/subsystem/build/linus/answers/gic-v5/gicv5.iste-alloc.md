- No lock is taken in `gicv5_irs_iste_alloc()`, and the valid bit is not
  rechecked after the first test.
- Serialisation: `root->mutex` of `struct irq_domain`, taken by the
  irqdomain core, for example in `__irq_domain_alloc_irqs()`, before any
  `.alloc` callback runs.
- The LPI domain is the root of its hierarchy, so child domains share that
  mutex; for example the IPI domain created in
  `drivers/irqchip/irq-gic-v5.c`.
- Only caller: `gicv5_irq_lpi_domain_alloc()`.
- **Unsafe usage**: calling `gicv5_irs_iste_alloc()` without the LPI
  domain's `root->mutex` held.
  - Unsafe: two callers can both see the level 1 entry invalid, both store
    an address and both write `GICV5_IRS_MAP_L2_ISTR`.
  - Safe: from an irqdomain `.alloc` callback, as
    `gicv5_irq_lpi_domain_alloc()` does.
- Order: the level 1 entry is stored first, then maintenance covers both
  the level 2 table and the entry, then the register write.
- Non-coherent maintenance differs by object: `dcache_clean_inval_poc()`
  over the level 2 table, `dcache_clean_poc()` (clean only) over the one
  level 1 entry.
- Failed wait: the level 1 entry is set to 0, the level 2 table is freed
  with `kfree()`, and the poll's error is returned.
