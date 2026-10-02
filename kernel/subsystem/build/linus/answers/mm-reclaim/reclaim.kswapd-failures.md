- `kswapd_failures`: an `atomic_t`; `kswapd_test_hopeless()`,
  `kswapd_clear_hopeless()` and `kswapd_try_clear_hopeless()` are defined in
  `mm/vmscan.c`.
- Increment: `balance_pgdat()` counts a failure only if `!sc.nr_reclaimed` and
  the run did not start with a watermark boost (`!boosted`).
- Reset after reclaim: `shrink_node()` and `lru_gen_shrink_node()` call
  `kswapd_try_clear_hopeless(pgdat, sc->order, sc->reclaim_idx)` when the pass
  reclaimed something.
- `kswapd_try_clear_hopeless()`: resets only if `pgdat_balanced()` is true for
  that order and index; progress that leaves the node unbalanced resets
  nothing.
- `free_frozen_page_commit()` in `mm/page_alloc.c`: resets with
  `kswapd_clear_hopeless()`, with no `pgdat_balanced()` test, when it clears
  `ZONE_BELOW_HIGH` on a hopeless node and
  `next_memory_node(pgdat->node_id) < MAX_NUMNODES`.
- `demotion_enabled_store()` in `mm/memory-tiers.c`: resets every online node
  when demotion goes from off to on.
- `prepare_kswapd_sleep()` and the body of `balance_pgdat()`: contain no reset;
  `balance_pgdat()` reaches `kswapd_try_clear_hopeless()` only through
  `shrink_node()`.
- `kswapd_clear_hopeless()`: does not wake kswapd; kswapd runs again when it
  is next woken, for example by `wakeup_kswapd()`.
- `skip_throttle_noprogress()` on a hopeless node: returns true for
  `VMSCAN_THROTTLE_CONGESTED` as well as `VMSCAN_THROTTLE_NOPROGRESS`.
