- Write bit: `madvise_free_pte_range()` leaves it untouched; only accessed and
  dirty are cleared.
- Next write without hardware dirty tracking: `handle_pte_fault()` finds
  `pte_write()` true and sets dirty; `do_wp_page()` is not called.
- Reclaim side for a PTE-mapped folio lives in `ttu_anon_folio()` and
  `ttu_anon_lazyfree_folio()` in `mm/rmap.c`, reached from
  `try_to_unmap_one()`.
- `ttu_anon_lazyfree_folio()` order: dirty test first, refcount test second.
- Dirty folio, VMA not `VM_DROPPABLE`: `folio_set_swapbacked()`, return false.
- Clean folio with `ref_count != 1 + map_count`: returns false and does not
  call `folio_set_swapbacked()`; the folio stays lazyfree.
- `VM_DROPPABLE`: skips only the dirty test; the refcount test still applies.
- On false, `try_to_unmap_one()` restores the entries with `set_ptes()` and
  aborts the walk.
- Large lazyfree folios are unmapped as a batch (`folio_unmap_pte_batch()`);
  `get_and_clear_ptes()` returns dirty merged over the batch, so one dirty
  entry keeps the whole folio.
- `folio_mark_lazyfree()` is in `mm/folio.c` and only queues the folio;
  `lru_lazyfree()` clears swapbacked when the batch drains.
