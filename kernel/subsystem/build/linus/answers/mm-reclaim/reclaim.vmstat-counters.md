- Scan, steal, demote, refill and rotate counters: all are
  `enum node_stat_item` in `include/linux/mmzone.h`, none is an
  `enum vm_event_item`. This covers `PGSCAN_KSWAPD` and `PGSTEAL_KSWAPD` with
  their per-reclaimer siblings, `PGDEMOTE_KSWAPD` with its siblings,
  `PGSCAN_ANON`, `PGSCAN_FILE`, `PGSTEAL_ANON`, `PGSTEAL_FILE`, `PGREFILL`,
  `PGROTATE_ANON` and `PGROTATE_FILE`.
- Helper: `mod_lruvec_state()`, in `mm/memcontrol.c` under `CONFIG_MEMCG`,
  one call per counter; it updates the node, the memcg and the lruvec.
  `count_vm_events()` and `count_memcg_events()` take `enum vm_event_item`
  and do not apply.
- `cgroup_reclaim(sc)`: does not guard any of these updates; memcg-limit
  reclaim counts in the node totals too.
- `mod_node_page_state()` alone on one of these items: updates the node and
  loses the memcg and lruvec share.
- `memcg_node_stat_items[]` in `mm/memcontrol.c`: an item missing from it
  makes `__mod_memcg_lruvec_state()` hit `WARN_ONCE()` and skip the memcg
  and lruvec update.
- `PGROTATE_ANON`, `PGROTATE_FILE`: pages scanned but not reclaimed, plus
  pages `shrink_active_list()` keeps active; `prepare_scan_control()` reads
  them with `lruvec_page_state_monotonic()` to build `lruvec->cost[]`.
- `PGROTATED`: a separate vm event, counted with `__count_vm_events()` in
  `lru_move_tail()` and one other site in `mm/folio.c`, with no memcg copy.
  There is no mm/swap.c in this tree.
- Still vm events in reclaim: `PGSCAN_SKIP` (`__count_zid_vm_events()`),
  `PGACTIVATE` (`count_vm_events()` plus `count_memcg_folio_events()` in
  `shrink_folio_list()`), `PGDEACTIVATE` (`count_vm_events()` plus
  `count_memcg_events()` in `shrink_active_list()`),
  `PGSCAN_DIRECT_THROTTLE`.
- __count_memcg_events(): not in this tree; use `count_memcg_events()`.
- `reclaimer_offset()`: the result is added to a `enum node_stat_item` base;
  `CHECK_RECLAIMER_OFFSET()` holds the `BUILD_BUG_ON()` layout checks.
