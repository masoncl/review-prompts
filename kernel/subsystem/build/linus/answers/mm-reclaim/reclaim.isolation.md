- `folio_isolate_lru()` order: `folio_test_clear_lru()`, then `folio_get()`,
  then `folio_lruvec_lock_irq()`, `lruvec_del_folio()`,
  `lruvec_unlock_irq()`. The reference is taken only after the flag is won,
  and before the lock.
- `folio_isolate_lru()` return: `bool`, `false` only when `PG_lru` was
  already clear. It returns no error code.
- `isolate_lru_folios()` tests, in order: `folio_zonenum()` against
  `sc->reclaim_idx`, `folio_test_lru()`, `!sc->may_unmap && folio_mapped()`,
  `folio_try_get()`, `folio_test_clear_lru()`.
- `isolate_lru_folios()` has no test of unevictable, dirty, writeback or CMA
  and takes no isolation mode; there is no __isolate_lru_folio_prepare() and
  no skip_cma() in this tree.
- Zone test in `isolate_lru_folios()`: rejects only while fewer than
  `SWAP_CLUSTER_MAX_SKIPPED` folios have been skipped in this call; after
  that a folio above `sc->reclaim_idx` runs the remaining tests and can be
  isolated.
- Rejected folios in `isolate_lru_folios()`: none stays in place. Every
  visited folio gets `list_move()`: to `dst`, to `folios_skipped` (zone), or
  to the head of `src` (all other rejections).
- `isolate_lru_folios()` does not call `lruvec_del_folio()`; LRU sizes are
  fixed once after the loop by `update_lru_sizes()`.
- `folio_put()` after a lost `folio_test_clear_lru()` in
  `isolate_lru_folios()`: no assertion accompanies it.
- Flags on a classic list: only `PG_lru` changes in both functions.
- Flags on an MGLRU list: `folio_isolate_lru()` reaches
  `lru_gen_del_folio()` in `include/linux/mm_inline.h` with
  `reclaiming == false`, which clears the `LRU_GEN_MASK` bits and sets
  `PG_active` when the folio was in one of the two youngest generations.
- `isolate_folio()` (MGLRU): does not clear `PG_reclaim`; it clears the
  `LRU_REFS_MASK` bits when `PG_referenced` is clear, and passes
  `reclaiming == true`, so `PG_active` is not set.
