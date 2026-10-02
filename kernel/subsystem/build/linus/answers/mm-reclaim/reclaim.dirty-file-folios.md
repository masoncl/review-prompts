- `struct address_space_operations` has no writepage member; `pageout()`
  calls `shmem_writeout()` or `swap_writeout()` directly.
- There is no writeout() or is_page_cache_freeable() helper; the refcount
  test, `folio_set_reclaim()` and its clearing are inline in `pageout()`.
- Dirty file-LRU folio: the `NR_VMSCAN_IMMEDIATE`, `folio_set_reclaim()`,
  `activate_locked` branch is unconditional; there is no kswapd test and no
  PGDAT_DIRTY flag.
- Flusher wakeup: in `handle_reclaim_writeback()`, called from
  `shrink_inactive_list()` and from `evict_folios()`.
- `swap_writeout()` returns 0 with no I/O and no writeback when
  `folio_free_swap()` succeeds, the folio is zero-filled, or `zswap_store()`
  takes it; `pageout()` then clears `PG_reclaim`.
- After the zero-filled and `zswap_store()` cases the folio is clean and can
  be freed in the same pass; after `folio_free_swap()` it is dirty and goes
  to `keep`.
- `swap_writeout()` returns `AOP_WRITEPAGE_ACTIVATE`, folio redirtied and
  still locked, when `zswap_store()` failed and
  `mem_cgroup_zswap_writeback_enabled()` is false.
- `shmem_writeout()` returns `AOP_WRITEPAGE_ACTIVATE`, folio redirtied and
  locked, at its `redirty` label: for example `SHMEM_F_LOCKED`, `noswap`, no
  swap pages, or a failed split.
- `shmem_writeout()` success: the folio has moved from the page cache to the
  swap cache, so `folio_mapping()` changes across `pageout()`.
