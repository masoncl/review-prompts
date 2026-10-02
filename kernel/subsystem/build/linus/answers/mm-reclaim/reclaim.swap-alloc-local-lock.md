- `swap_cluster_populate()` is in `mm/swapfile.c`; `swap_cluster_alloc_table()`
  is the bare allocator it calls, and drops no lock itself.
- `percpu_swap_cluster.lock` is taken with `local_lock()`, in
  `folio_alloc_swap()` and `swap_alloc_hibernation_slot()`.
- `swap_cluster_populate()` is reached only from `isolate_lock_cluster()`, for
  a cluster that had `CLUSTER_FLAG_FREE`.
- `swap_cluster_populate()` asserts the local lock, `ci->lock`, and
  `si->global_cluster_lock` when `SWP_SOLIDSTATE` is clear.
- Sleeping attempt: fixed flags `__GFP_HIGH | __GFP_NOMEMALLOC | GFP_KERNEL`;
  no caller supplies a gfp mask.
- After relocking there is no recheck and no spare table to free; the cluster
  stayed off every list with `CLUSTER_FLAG_NONE`.
- Allocation failure: the cluster goes back to `si->free_clusters`, `ci->lock`
  is dropped, NULL is returned with the local lock and
  `si->global_cluster_lock` still held.
- `alloc_swap_scan_list()` on `si->free_clusters` may therefore sleep and
  change CPU; on an `SWP_SOLIDSTATE` device `alloc_swap_scan_cluster()` writes
  the cache of the CPU it ends on.
- **Potentially unsafe usage**: calling `isolate_lock_cluster()` without
  `percpu_swap_cluster.lock`.
  - Unsafe: on `si->free_clusters`; `swap_cluster_populate()` asserts the
    local lock and, when the atomic allocation fails, unlocks it.
  - Safe: on `si->full_clusters`, as `swap_reclaim_full_clusters()` does from
    `swap_reclaim_work()`; no cluster there has `CLUSTER_FLAG_FREE`.
