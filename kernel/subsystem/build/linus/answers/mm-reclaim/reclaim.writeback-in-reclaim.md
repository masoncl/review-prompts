- `writeback_throttling_sane()`: true for global reclaim
  (`sc->target_mem_cgroup` NULL); for cgroup reclaim, true only on cgroup v2
  built with `CONFIG_CGROUP_WRITEBACK`; always true without `CONFIG_MEMCG`.
- Case 2 has four alternatives: `writeback_throttling_sane()`,
  `!folio_test_reclaim()`, `!may_enter_fs()`, or a non-NULL mapping with
  `mapping_writeback_may_deadlock_on_reclaim()`
  (`AS_WRITEBACK_MAY_DEADLOCK_ON_RECLAIM`).
- Case 2 does not test `current_is_kswapd()`; only case 1 does.
- Wait (case 3) needs all of: cgroup reclaim without sane throttling,
  `PG_reclaim` already set, `may_enter_fs()` true, mapping not flagged.
- `may_enter_fs()` false prevents the wait; it never causes it.
- `may_enter_fs()`: there is no SWP_FS_OPS; with only `__GFP_IO` a swap-cache
  folio passes unless the device's `ops->flags` has
  `SWAP_OPS_F_REQUIRE_NOFS`. It makes no `PG_private` test.
- `stat->nr_immediate`: summed into `sc->nr.immediate` by
  `handle_reclaim_writeback()`; the stall is
  `reclaim_throttle(pgdat, VMSCAN_THROTTLE_WRITEBACK)` in `shrink_node()`,
  for kswapd only.
- `PGDAT_WRITEBACK`: set by kswapd in `shrink_node()` when
  `sc->nr.writeback` is non-zero and equals `sc->nr.taken`.
