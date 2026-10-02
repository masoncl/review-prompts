- `folio_copy()` in `mm/util.c`: called directly. There is no
  folio_migrate_copy().
- `migrate_huge_page_move_mapping()`: calls `folio_mc_copy()`, so the
  hugetlb callback can sleep.
- `__buffer_migrate_folio()`: takes `mapping->i_private_lock` only with
  `check_refs`, and only around the `b_count` scan.
- **Potentially unsafe usage**: calling `folio_copy()`, `folio_mc_copy()`,
  `migrate_folio()` or `filemap_migrate_folio()` under a spinlock.
  - Unsafe: when the folio can be large; the copy calls `cond_resched()`
    between pages.
  - Safe: order-0 folios only, as `aio_migrate_folio()` does with
    `folio_copy()`; `aio_setup_ring()` allocates the ring folios with no
    order. The copy loop in `folio_copy()` defines it: no `cond_resched()`
    for one page.
  - Safe: scan under the lock, drop it, then call the helper, as
    `__buffer_migrate_folio()` does; `BH_Migrate` keeps atomic lookups out.
- **Unsafe usage**: calling `folio_migrate_mapping()` with interrupts
  disabled, for a folio that has a mapping.
  `__folio_migrate_mapping()` ends with `local_irq_enable()`.
  - Safe: call it with interrupts enabled and take the irq-disabling lock
    afterwards, as `aio_migrate_folio()` does.
