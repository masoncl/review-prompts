- `apply_proportional_protection()` in `mm/vmscan.c`: does the scan scaling;
  `get_scan_count()` and MGLRU's `get_nr_to_scan()` both call it.
- There is no mem_cgroup_size() here; `mem_cgroup_protection()` returns the
  usage through its fifth argument, next to `min` and `low`.
- Formula: `scan -= scan * protection / (usage + 1)`, with
  `usage = max(usage, protection)`.
- Protection used: `low` only if `!sc->memcg_low_reclaim && low > min`, which
  also sets `sc->memcg_low_skipped`; otherwise `min`, on the first pass too.
- `SWAP_CLUSTER_MAX` floor: applied to the scaled size before
  `>> sc->priority`, and only when `min` or `low` is non-zero.
- Low override: `do_try_to_free_pages()` is the only place that sets
  `sc->memcg_low_reclaim`.
- `balance_pgdat()` and `__node_reclaim()`: reach `shrink_node()` without that
  retry, so on the classic LRU kswapd and node reclaim always skip a memcg
  that is below low in `shrink_node_memcgs()`.
- Retry order in `do_try_to_free_pages()`: it returns first if anything was
  reclaimed or `sc->compaction_ready` is set; then it retries with
  `sc->memcg_full_walk`, then with `sc->force_deactivate` if
  `sc->skipped_deactivate`, and only then with `sc->memcg_low_reclaim` if
  `sc->memcg_low_skipped`.
- MGLRU root reclaim, when not `lru_gen_switching()`: `shrink_node()` calls
  `lru_gen_shrink_node()` and does not reach `shrink_node_memcgs()`.
- `shrink_one()`: tests `mem_cgroup_below_min()` and `mem_cgroup_below_low()`
  but does not call `mem_cgroup_calculate_protection()`.
- `lru_gen_age_node()`: the only caller of
  `mem_cgroup_calculate_protection()` for MGLRU root reclaim; kswapd runs it.
- `shrink_one()` on a memcg below low: its test does not read
  `sc->memcg_low_reclaim`; it returns `MEMCG_LRU_TAIL` while its lruvec is not
  at `MEMCG_LRU_TAIL`, and calls `try_to_shrink_lruvec()` when its lruvec is
  already at `MEMCG_LRU_TAIL`; for an online memcg `get_nr_to_scan()` still
  scales the target with `apply_proportional_protection()`.
