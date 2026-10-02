- Comparison in `too_many_isolated()` in `mm/vmscan.c`: true when
  `isolated > inactive`; `inactive` is shifted right by 3 first when
  `gfp_has_io_fs(sc->gfp_mask)`. There is no halving.
- `writeback_throttling_sane()` false means no limit: that is reclaim with
  `sc->target_mem_cgroup` set on cgroup v1, or on any hierarchy without
  `CONFIG_CGROUP_WRITEBACK`. Global direct reclaim, and cgroup v2 memcg
  reclaim with `CONFIG_CGROUP_WRITEBACK`, are limited.
- Fatal signal after the stall in `shrink_inactive_list()`: returns
  `SWAP_CLUSTER_MAX`. The return of 0 is for a second trip round the loop.
- `wake_throttle_isolated()`: called only from the two `too_many_isolated()`
  functions (`mm/vmscan.c`, `mm/compaction.c`), when the comparison there is
  false. Putback wakes nobody; a sleeper otherwise waits out the `HZ/50`
  timeout.
- Task that `reclaim_throttle()` does not put to sleep (see "Exempt tasks"
  under "Reclaim throttling"): goes straight to the second check in
  `shrink_inactive_list()`, which returns 0 if `too_many_isolated()` is still
  true.
- `NR_ISOLATED_ANON` and `NR_ISOLATED_FILE`: node-wide, and raised by
  isolators that `too_many_isolated()` in `mm/vmscan.c` never blocks, for
  example `shrink_active_list()`, kswapd in `shrink_inactive_list()`, and
  `isolate_migratepages_block()`.
- MGLRU: `evict_folios()` neither calls `too_many_isolated()` nor changes
  `NR_ISOLATED_ANON` or `NR_ISOLATED_FILE`, so folios it holds are invisible
  to both `too_many_isolated()` functions.
