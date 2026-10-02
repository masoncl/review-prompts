- There is no zone_watermark_ok_safe() in this tree. `pgdat_balanced()` in
  `mm/vmscan.c` open-codes the check and passes the count to
  `__zone_watermark_ok()`.
- `pgdat_balanced()` reads `NR_FREE_PAGES_BLOCKS` instead of `NR_FREE_PAGES`
  when `defrag_mode` is set and the order is non-zero, and compares it with
  the same `percpu_drift_mark`.
- Unconditional `zone_page_state_snapshot()` of `NR_FREE_PAGES`, with no look
  at `percpu_drift_mark`: `should_reclaim_retry()`, `allow_direct_reclaim()`
  and `compaction_zonelist_suitable()`.
- Cheap read: every caller of `zone_watermark_ok()` and
  `zone_watermark_fast()`, which includes reclaim-side tests such as
  `compaction_ready()`; `compaction_suitable()` also passes the cheap count,
  to `__zone_watermark_ok()`.
- `percpu_drift_mark` has one writer, `refresh_zone_stat_thresholds()`, with
  no else branch: when the drift fits in the low-min gap the field keeps its
  previous value.
- `set_pgdat_percpu_threshold()` skips zones whose `percpu_drift_mark` is 0,
  so kswapd's threshold switching in `kswapd_try_to_sleep()` only affects
  zones that have the mark set.
- `zone_page_state_snapshot()` is not exact: it sums the per-CPU deltas of
  online CPUs with no synchronisation.
- Without `CONFIG_SMP`: both reads are the same, and
  `refresh_zone_stat_thresholds()` is an empty stub in
  `include/linux/vmstat.h`, so `percpu_drift_mark` is never set.
