| Jump | Bound |
|---|---|
| `retry` after dropping `ac->nodemask` or gaining reserves | once per call; `can_retry_reserves` |
| `retry` without direct reclaim, `defrag_mode`, `__GFP_KSWAPD_RECLAIM` | once per `restart`; clears `ALLOC_NOFRAGMENT` |
| `retry` after the `compact_first` pass | once per `restart`; clears `compact_first` |
| `retry` from `should_reclaim_retry()` | `no_progress_loops` over `MAX_RECLAIM_RETRIES`; reset on progress at a non-costly order |
| `retry` from `should_compact_retry()` | `compaction_retries`, `compact_priority`; see below |
| `retry` under `defrag_mode` after both declined | once per `restart`; clears `ALLOC_NOFRAGMENT` |
| `retry` after `__alloc_pages_may_oom()` progress | none |
| `retry` for `__GFP_NOFAIL` at `nopage` | none |
| `restart` from any of the three check sites | no counter |

- `ALLOC_NOFRAGMENT` without `CONFIG_ZONE_DMA32`: defined as 0 in
  `mm/page_alloc.h`, so neither `defrag_mode` jump is taken.
- `should_reclaim_retry()` past `MAX_RECLAIM_RETRIES`: still returns true if
  `unreserve_highatomic_pageblock()` with `force` released a block.
- `should_compact_retry()`: `compaction_retries` advances only on
  `COMPACT_SUCCESS`, with the limit `MAX_COMPACT_RETRIES` divided by 4 for a
  costly order.
- `should_compact_retry()` on `COMPACT_SKIPPED`: returns
  `compaction_zonelist_suitable()`, with no counter.
- `should_compact_retry()` priority floor: `MIN_COMPACT_COSTLY_PRIORITY` for
  a costly order, `MIN_COMPACT_PRIORITY` otherwise.
- `restart` from the nodemask branch of `check_retry_cpuset()`: at most once
  per call, since it sets `ac->nodemask` to NULL; the cookie branches need a
  new outside change after each `restart`.
- `restart` recomputes: both cookies, `compaction_retries`,
  `no_progress_loops`, `compact_result`, `compact_priority`, `compact_first`,
  `alloc_flags` from `alloc_flags_slowpath()`, and `ac->preferred_zoneref`.
- `restart` does not reset: `can_retry_reserves`, `alloc_start_time`, or an
  `ac->nodemask` already set to NULL.
- `retry` with reserve flags: `alloc_flags` is rebuilt from
  `alloc_flags_cma()`, the reserve flags, `ac->alloc_flags` and the
  `ALLOC_KSWAPD` bit only; `ALLOC_CPUSET`, `ALLOC_MIN_RESERVE` and
  `ALLOC_NOFRAGMENT` are lost until the next `restart`.
- `check_retry_cpuset()` detects two things, both only with
  `cpusets_enabled()`: `ac->nodemask` no longer intersecting the cpuset
  (`cpuset_nodemask_valid_mems_allowed()`), and a change of
  `current->mems_allowed_seq` since `read_mems_allowed_begin()`.
- `check_retry_zonelist()`: `read_seqretry()` on `zonelist_update_seq`, which
  `__build_all_zonelists()` writes; there is no zonelist_iter_retry() here.
- `check_retry_zonelist()` without `CONFIG_MEMORY_HOTREMOVE`: returns the
  cookie, which `zonelist_iter_begin()` set to 0, so it never restarts.
