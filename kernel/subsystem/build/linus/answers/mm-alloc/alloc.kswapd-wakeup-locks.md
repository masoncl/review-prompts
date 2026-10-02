- `fill_pool()` in `lib/debugobjects.c`: starts from
  `__GFP_HIGH | __GFP_NOWARN` and adds `__GFP_KSWAPD_RECLAIM` when
  `preemptible() || system_state < SYSTEM_SCHEDULING`.
- `fill_pool()` without the bit: only in non-preemptible context once
  `system_state` has reached `SYSTEM_SCHEDULING`, where the caller may hold
  locks.
- `callback_lock` in `kernel/cgroup/cpuset.c`: `wakeup_kswapd()` can take it
  through `cpuset_zone_allowed()`, before any waitqueue test.
- `callback_lock` is reached only with cpusets enabled, `in_interrupt()`
  false, without `__GFP_HARDWALL`, on cpuset v1, for a node outside
  `current->mems_allowed`; see `cpuset_current_node_allowed()`.
- `wakeup_kswapd()` calls `wakeup_kcompactd()` only when the mask lacks
  `__GFP_DIRECT_RECLAIM`, in the branch for a hopeless node or a balanced
  node with no boosted watermark; `wakeup_kcompactd()` returns at once for
  order 0.
- Fast path: `rmqueue()` calls `wakeup_kswapd()` when `ALLOC_KSWAPD` is set
  and the zone has `ZONE_BOOSTED_WATERMARK`; `alloc_flags_nofragment()` sets
  `ALLOC_KSWAPD` from the mask.
- `gfp_nested_mask()`: keeps `__GFP_KSWAPD_RECLAIM` if the caller had it
  (both `GFP_KERNEL` and `GFP_ATOMIC` contain it) and never adds it.
- `gfp_nested_mask()` users do not strip the bit for the caller:
  `stack_depot_save_flags()` and `add_stack_record_to_list()` skip the
  allocation when `gfpflags_allow_spinning()` is false.
- Masks with neither reclaim bit, for example: `gfp_nolock` in
  `mm/page_alloc.c`, and the `__GFP_NOWARN` that `__reset_page_owner()`
  passes.
