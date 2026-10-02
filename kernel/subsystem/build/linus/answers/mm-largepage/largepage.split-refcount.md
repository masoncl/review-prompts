- There is no can_split_folio() here; the precheck is inline in
  `__folio_split()`: `folio_expected_ref_count(folio) != folio_ref_count(folio) - 1`.
- Precheck position: after `filemap_release_folio()` and after the anon_vma
  or `i_mmap_rwsem` lock, before `unmap_folio()`.
- Freeze: `folio_ref_freeze(folio, folio_cache_ref_count(folio) + 1)` in
  `__folio_freeze_and_split_unmapped()`.
- `folio_cache_ref_count()` in `mm/huge_memory.c`: counts page cache or swap
  cache references only, so a mapping that survived `unmap_folio()` or a
  remaining `PG_private` fails the freeze.
- `folio_split_unmapped()`: same precheck with the same `- 1`.
- New pieces and the original: unfrozen to `folio_cache_ref_count() + 1`, not
  to `folio_expected_ref_count() + 1`.
- Removed by the split itself: mapcount references (`unmap_folio()`) and the
  `PG_private` reference (`filemap_release_folio()`).
- Per-CPU LRU batches: do not hold large folios; `folio_may_be_lru_cached()`
  in `mm/internal.h` is false for them and `__folio_batch_add_and_move()`
  flushes at once.
- `deferred_split_scan()`: its reference is taken in
  `deferred_split_isolate()` and dropped by `deferred_split_scan()` after its
  split attempt on that folio.
- A second reference of the caller's own on the same folio: stays until the
  caller drops it; `cmp_and_merge_page()` in `mm/ksm.c` drops it, then
  splits.
