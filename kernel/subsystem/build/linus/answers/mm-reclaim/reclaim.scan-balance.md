- Cost inputs: there is no lru_note_cost() or lru_note_cost_refault() in this
  tree, and `struct lruvec` has no `anon_cost` or `file_cost` field.
- `lruvec->cost[]` (`struct lru_cost` in `include/linux/mmzone.h`): holds the
  costs, under `lruvec->cost_lock`.
- `prepare_scan_control()`: the only place that updates and decays
  `lruvec->cost[]`, for the target lruvec; it copies the result to
  `sc->anon_cost` and `sc->file_cost`.
- Cost sources: deltas of `PGROTATE_ANON + f`, `WORKINGSET_RESTORE_BASE + f`
  and, for anon only, `NR_VMSCAN_WRITE`; IO events weigh `SWAP_CLUSTER_MAX`
  times a rotation.
- Order of tests in `get_scan_count()`: `SWAPPINESS_ANON_ONLY` comes first,
  before `sc->may_swap` and `can_reclaim_anon_pages()`.
- `SWAPPINESS_ANON_ONLY` when `can_reclaim_anon_pages()` is false: every entry
  of `nr[]` is zeroed and the function returns; file is not scanned as a
  fallback.
- `SWAPPINESS_ANON_ONLY`: `MAX_SWAPPINESS + 1` in `mm/internal.h`.
- Swappiness `MAX_SWAPPINESS` (200): has no test of its own and is not
  `SCAN_ANON`; under `SCAN_FRACT` its file weight is 0.
- Swappiness 0: the zero test gives `SCAN_FILE` only when
  `cgroup_reclaim(sc)`; global reclaim falls through, and gets `SCAN_FRACT`
  with an anon weight of 0 unless `sc->file_is_tiny` or `sc->cache_trim_mode`
  is set.
- `SCAN_EQUAL`: needs `sc->priority == 0`, the most aggressive pass, and
  non-zero swappiness.
- `can_reclaim_anon_pages()`: tests `get_nr_swap_pages()` or
  `mem_cgroup_get_nr_swap_pages()`, then `can_demote()`; it does not read
  `total_swap_pages`.
- `calculate_pressure_balance()`: holds the `SCAN_FRACT` weights.
- MGLRU, when `lru_gen_enabled()` and not `lru_gen_switching()`:
  `prepare_scan_control()` returns before it sets anything; `shrink_lruvec()`
  returns before it calls `get_scan_count()` when `!root_reclaim(sc)`, and
  root reclaim returns from `shrink_node()` after `lru_gen_shrink_node()`.
