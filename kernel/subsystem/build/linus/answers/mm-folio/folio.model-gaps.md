- Models take a caller of `lruvec_stat_mod_folio()` to need `rcu_read_lock()`
  for the memcg lookup. `lruvec_stat_mod_folio()` in `mm/memcontrol.c` takes
  `rcu_read_lock()` itself.
- Models take `folio_end_writeback()` never to lock the folio or change the
  cache. For a `PG_dropbehind` folio in task context it trylocks and may
  remove the folio via `folio_unmap_invalidate()`;
  `folio_end_writeback_no_dropbehind()` does not.
- Models take `put_page()` to be a plain wrapper. On a slab or large-kmalloc
  page `put_page()` drops nothing; see `include/linux/mm.h`.
- Models take swap cache lookup to recheck like `filemap_get_entry()`.
  `swap_cache_get_folio()` in `mm/swap_state.c` only does `folio_try_get()`.
- Models name swap_cache_add_folio(). There is no swap_cache_add_folio()
  here; `__swap_cache_add_folio()` needs the cluster locked.
- Models take a lookup to leave `PG_dropbehind` alone.
  `__filemap_get_folio_mpol()` clears it on any folio it returns to a lookup
  without `FGP_DONTCACHE`.
