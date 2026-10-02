- `sort_folio()` cases in this tree:

| Folio | Action | Returns |
|---|---|---|
| not evictable | none | false |
| generation is not the oldest | `list_move()` to its own list | true |
| tier above `tier_idx`, or all bits set | `folio_inc_gen()`, `list_move()` | true |
| zone above `sc->reclaim_idx` | `folio_inc_gen()`, `list_move_tail()` | true |

- Unevictable folios: isolated like any other; `move_folios_to_lru()` culls
  them with `folio_putback_lru()`.
- Dirty and writeback folios: `sort_folio()` has no case for them; they are
  isolated and `shrink_folio_list()` decides.
- Promoted case: `sort_folio()` does not call `lru_gen_set_refs()`.
- `nr_to_scan`: `try_to_shrink_lruvec()` passes at most `MIN_LRU_BATCH`;
  `run_eviction()` passes at most `MAX_LRU_BATCH`.
- `scan_folios()` return: pages scanned, also when nothing was isolated; the
  isolated count comes back through `isolatedp`.
- `isolate_folios()`: switches to the other type only when a scan returned
  0; with pages scanned and none isolated it scans the same type again.
- `evict_folios()`: calls `try_to_inc_min_seq()` before isolation, and again
  after it when anything was scanned.
- Rejects are re-added by `lruvec_add_folio()`, with `reclaiming` false.
- Retry pass: for rejects that are not active, not mapped, not dirty and not
  under writeback; dirty folios are not retried.
- Dirty file rejects: `shrink_folio_list()` sets `PG_reclaim` and
  `PG_active`, so `lru_gen_folio_seq()` places them at `max_seq - 1`, or at
  `max_seq` with `PG_workingset`.
