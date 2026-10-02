- Expected count: `folio_expected_ref_count()` in `include/linux/mm.h`.
  There is no folio_expected_refs().
- `folio_expected_ref_count()`: swap cache references count for any folio;
  `mapping` and `PG_private` count only for non-anon folios.
- `folio_migrate_mapping()`: adds `extra_count + 1`, compares with
  `folio_ref_count()` for every folio, and returns `-EAGAIN` on mismatch
  before taking any lock.
- `__folio_migrate_mapping()` with no mapping: a large rmappable folio is
  still frozen with `folio_ref_freeze()`, to leave the deferred split
  queue; failure returns `-EAGAIN`. Other folios are not frozen.
- `__folio_migrate_mapping()` with a mapping: swap cache folios are frozen
  under `swap_cluster_get_and_lock_irq()`, not the xarray lock, and replaced
  with `__swap_cache_replace_folio()`.
- Xarray slot: not checked. The frozen count is the only test.
- `__folio_migrate_mapping()` makes no unlocked compare of its own.
  `__migrate_folio()` compares before `folio_mc_copy()` and passes the count
  down.
- Success: returns 0. MIGRATEPAGE_SUCCESS is not defined.
