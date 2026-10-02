| Item | `shrink_inactive_list()` | `evict_folios()` |
|---|---|---|
| `NR_ISOLATED_ANON + file` | `+nr_taken` under the lock, `-nr_taken` after putback | not touched |
| `PGSCAN_KSWAPD + reclaimer_offset(sc)`, `PGSCAN_ANON` or `PGSCAN_FILE` | `nr_scanned`: every page looked at, zone-skipped included | in `scan_folios()`, `isolated` only |
| `PGREFILL` | not here; `shrink_active_list()` adds `nr_scanned` | in `scan_folios()`, pages moved by `sort_folio()` |
| `PGSCAN_SKIP` | in `isolate_lru_folios()`: pages skipped for their zone | in `scan_folios()`: pages for which `isolate_folio()` failed |
| `sc->nr_reclaimed` | added by `shrink_lruvec()` from the return value | added in `evict_folios()`, each pass |
| `sc->nr` tallies, flusher wakeup | `handle_reclaim_writeback(nr_taken, ...)` | `handle_reclaim_writeback(isolated, ...)`, first pass only |
| Putback | `move_folios_to_lru()`, lock not held | `move_folios_to_lru()`, lock not held |
| `PGDEMOTE_KSWAPD + reclaimer_offset(sc)` | `stat.nr_demoted` | `stat.nr_demoted`, each pass |
| `PGSTEAL_KSWAPD + reclaimer_offset(sc)`, `PGSTEAL_ANON` or `PGSTEAL_FILE` | `nr_reclaimed` | `reclaimed`, each pass |
| `PGROTATE_ANON + file` | `nr_scanned - nr_reclaimed`, if positive | `nr_isolated - total_reclaimed`, if positive, once after the last pass |

- Helper for every `PG` row except `PGSCAN_SKIP`: `mod_lruvec_state()`,
  with no `cgroup_reclaim(sc)` test, in both functions.
- `handle_reclaim_writeback()`: fills `sc->nr.dirty`, `sc->nr.congested`,
  `sc->nr.writeback`, `sc->nr.immediate`, `sc->nr.taken` for both paths, and
  wakes the flushers when `stat->nr_unqueued_dirty == nr_taken`.
  `struct scan_control` has no unqueued_dirty or file_taken member in `nr`.
- lru_note_cost(): not in this tree. The rotation share of reclaim cost
  comes from `PGROTATE_ANON` and `PGROTATE_FILE`, which both paths update;
  `prepare_scan_control()` consumes them and returns early under MGLRU
  unless `lru_gen_switching()`.
- `move_folios_to_lru()`: takes only the list, locks each folio's lruvec
  itself, and its caller must not hold a lruvec lock.
- Freeing: neither function uncharges or frees after `shrink_folio_list()`;
  `shrink_folio_list()` and `move_folios_to_lru()` call
  `mem_cgroup_uncharge_folios()` and `free_unref_folios()` themselves. There
  is no mem_cgroup_uncharge_list() in this tree.
