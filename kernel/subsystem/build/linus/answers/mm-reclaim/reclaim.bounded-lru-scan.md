- **Potentially unsafe usage**: setting a filtered folio aside without adding
  it to the loop bound.
  - Unsafe: when no second counter caps the folios set aside; the lock is
    held with interrupts off for as long as the filter keeps rejecting.
  - Safe: `isolate_lru_folios()`: zone-ineligible folios do not add to
    `scan`, but `max_nr_skipped` counts them, in folios not pages, and at
    `SWAP_CLUSTER_MAX_SKIPPED` (`include/linux/swap.h`) the zone test stops
    applying, so each later folio adds to `scan`.
  - Safe: `scan_folios()`: `remaining` starts at `nr_to_scan` and drops by
    one per folio visited, whether sorted, isolated or skipped; it asserts
    `nr_to_scan <= MAX_LRU_BATCH`, and also stops a zone when `isolated` or
    `skipped_zone` reaches `MIN_LRU_BATCH`.
- `scan` and `total_scan` in `isolate_lru_folios()`: `scan` bounds the loop
  and excludes zone-skipped pages; `total_scan` includes them and is what
  `*nr_scanned` returns.
- **Unsafe usage**: leaving a visited folio at the tail of the list being
  scanned; each iteration takes the tail again with `lru_to_folio()`.
  - Safe: `list_move()` every visited folio, accepted or not, as
    `isolate_lru_folios()` does at its `move` label.
- **Potentially unsafe usage**: processing a whole LRU list under the lock.
  - Unsafe: when the list length is the only bound on one lock hold.
  - Safe: stop after `MAX_LRU_BATCH` folios, unlock, `cond_resched()`, lock
    again, as `lru_gen_change_state()` does around `fill_evictable()` and
    `drain_evictable()`.
- **Potentially unsafe usage**: `folio_put()` while holding the LRU lock.
  - Unsafe: when `PG_lru` may be set and the reference may be the last;
    `__page_cache_release()` in `mm/folio.c` then takes the lruvec lock.
  - Safe: drop the lock first, as `isolate_migratepages_block()` does at
    `isolate_fail_put`.
  - Safe: after `folio_test_clear_lru()` returned false, as in
    `isolate_lru_folios()`: `__page_cache_release()` takes the lock only
    when `folio_test_lru()` is true.
