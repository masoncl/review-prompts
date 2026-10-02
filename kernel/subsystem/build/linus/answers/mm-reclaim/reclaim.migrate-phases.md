- State between phases: stored in `dst->migrate_info` by
  `__migrate_folio_record()`. It shares a union with `private` and `swap`
  in `struct folio`; `dst->mapping` is not used.
- Flag names: `FOLIO_WAS_MAPPED` and `FOLIO_WAS_MLOCKED` in `mm/migrate.c`.
  There is no PAGE_WAS_MAPPED or PAGE_WAS_MLOCKED.
- Return values: both phases return 0 or a negative errno. MIGRATEPAGE_UNMAP
  and MIGRATEPAGE_SUCCESS are not defined.
- `migrate_folio_unmap()`: calls `get_new_folio()` before it touches `src`,
  so `-ENOMEM` needs no undo.
- movable_ops pages: the unmap phase locks both folios and records state
  without calling `try_to_migrate()`. The move phase calls
  `migrate_movable_ops_page()`, not `move_to_new_folio()`.
- Pairs still at `-EAGAIN` when the move passes run out:
  `migrate_folios_undo()` extracts the state and runs both undo helpers.
