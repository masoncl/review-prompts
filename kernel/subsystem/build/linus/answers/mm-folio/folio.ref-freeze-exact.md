- `folio_ref_unfreeze()`: stores the count it is given, which need not be the
  frozen one. `remove_mapping()` passes 1 and `__folio_migrate_mapping()`,
  for a folio with a mapping, passes `expected_count - nr`, which drops the
  cache references.
- Failed `folio_try_get()`: does not tell frozen from freed.
  `deferred_split_isolate()` in `mm/huge_memory.c` treats it as freed and
  unlinks the folio.
- `__folio_freeze_and_split_unmapped()`: for that reason, for an anon folio
  of order > 1, takes the `deferred_split_lru` lock before
  `folio_ref_freeze()`, with count `folio_cache_ref_count(folio) + 1`.
- `ksm_get_folio()`: the opposite case; it spins on `folio_try_get()` while
  `folio_test_swapcache()` is set, because the folio may be frozen for
  migration.
