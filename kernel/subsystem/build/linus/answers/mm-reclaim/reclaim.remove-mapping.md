- Page-cache folio: `spin_lock(&mapping->host->i_lock)`, then
  `xa_lock_irq(&mapping->i_pages)`.
- Swap-cache folio: only the swap cluster lock, through
  `swap_cluster_get_and_lock_irq()` in `mm/swap.h`; no `i_lock`, no
  `i_pages` lock.
- IRQ-off form of the cluster lock: `__memcg1_swapout()` runs under it and
  relies on interrupts being disabled.
- Freeze count: `1 + folio_nr_pages(folio)` for both kinds of folio.
- `i_lock` is held for `inode_lru_list_add()`; there is no inode_add_lru().
