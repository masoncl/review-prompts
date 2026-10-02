- Names: there is no swap_duplicate(), swap_free(), put_swap_folio(),
  __delete_from_swap_cache(), swap_writepage() or SWAP_HAS_CACHE here. The
  count is raised by `folio_dup_swap()` and dropped by `folio_put_swap()`
  (`mm/swapfile.c`); the write is `swap_writeout()` (`mm/page_io.c`); the
  cache pin is the swap table entry that holds the folio.
- `folio_alloc_swap()`: requires the folio locked and uptodate and not yet
  in the swap cache; it adds the folio itself, and the slots start with
  count 0.
- Per-PTE sequence: `try_to_unmap_one()` clears the PTE, then
  `ttu_anon_swapbacked_folio()` in `mm/rmap.c` runs `folio_dup_swap()`,
  `arch_unmap_one()`, `folio_try_share_anon_rmap_pte()`, `set_pte_at()` in
  that order.
- Unmap failure after the count was raised: `ttu_anon_swapbacked_folio()`
  calls `folio_put_swap()` for that page; `try_to_unmap_one()` then restores
  the PTE with `set_ptes()` and aborts the walk.
- `activate_locked` in `shrink_folio_list()`: calls `folio_free_swap()` only
  when `mem_cgroup_swap_full()` or `folio_test_mlocked()`; it returns false
  while any slot of the folio has a count or the folio is under writeback,
  so a partly unmapped folio keeps its slots.
- Folio lock during the write: not held throughout. `__swap_writepage()`
  calls `folio_start_writeback()` then `folio_unlock()`; in that window
  `folio_swapcache_freeable()` refuses a folio under writeback.
- After `PAGE_SUCCESS`: `shrink_folio_list()` retakes the lock with
  `folio_trylock()` and retests dirty and writeback before
  `__remove_mapping()`.
- `__swap_writepage()`: does not submit on its own; it queues the folio in
  the caller's `struct swap_io_ctx` with `swap_add_folio()`, which submits
  the earlier batch first when the folio cannot merge with it, and submits
  the folio's batch when that is full or the device is
  `SWP_SYNCHRONOUS_IO`; otherwise the I/O starts at `swap_write_submit()`,
  which `shrink_folio_list()` calls last.
- Write error: `swap_write_end()` in `mm/page_io.c` redirties the page and
  clears the reclaim flag; there is no __end_swap_bio_write().
- `arch_prepare_to_swap()` failure in `swap_writeout()`: folio redirtied and
  unlocked, negative error returned, not `AOP_WRITEPAGE_ACTIVATE`.
- Removal: `__remove_mapping()` takes the cluster lock with
  `swap_cluster_get_and_lock_irq()` and calls `__swap_cache_del_folio()`,
  which stores the shadow and frees every slot whose count is 0 in the same
  step. No separate call drops a cache reference afterwards.
