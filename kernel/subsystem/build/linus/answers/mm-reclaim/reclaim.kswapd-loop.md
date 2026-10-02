- `sc.may_writepage`: set to `!nr_boost_reclaim` on every iteration, like
  `sc.may_swap`.
- `mm/vmscan.c` has no test of `sc.priority < DEF_PRIORITY - 2` for writeback
  and no reference to `laptop_mode`.
- `sc.priority--`: runs only when `raise_priority || !nr_reclaimed`, not on
  every pass.
- `kswapd_shrink_node()`: returns
  `max(sc->nr_scanned, sc->nr_reclaimed - nr_reclaimed) >= sc->nr_to_reclaim`,
  so pages reclaimed in the pass count as well as pages scanned; true clears
  `raise_priority`.
- MGLRU: `set_initial_priority()`, called from `lru_gen_shrink_node()`, can
  lower `sc.priority` from `DEF_PRIORITY` to as little as `DEF_PRIORITY / 2`
  inside the first pass.
- Not loop exits: `balance_pgdat()` tests neither
  `sc.nr_reclaimed >= sc.nr_to_reclaim` nor `kswapd_failures`.
- Unbalanced while boost reclaim is pending: `nr_boost_reclaim` is cleared and
  the loop restarts at `DEF_PRIORITY`; balanced with boost pending keeps
  reclaiming.
- Stop test: `kthread_freezable_should_stop()`; the loop breaks if it returns
  true or reports that the task was frozen.
- Aging call: `kswapd_age_node()`; there is no age_active_anon() here.
- After the loop: if `!sc.nr_reclaimed`, `sc.priority < 1`,
  `sc.cache_trim_mode_failed` is set and `sc.no_cache_trim_mode` is clear, it
  sets `sc.no_cache_trim_mode` and restarts at `DEF_PRIORITY`.
- `goto out` on a balanced node: skips that restart and the failure count.
