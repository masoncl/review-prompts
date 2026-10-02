- `folio_alloc_swap()` takes only the folio; there is no `gfp_t` argument.
- Return values: 0; `-EAGAIN` for a large folio without `CONFIG_THP_SWAP`;
  `-EINVAL` above `SWAPFILE_CLUSTER` pages; `-ENOMEM` for no slots or a failed
  memcg charge. It never returns `-ENOSPC`.
- On success the slots hold PFN entries with swap count 0; only the swap cache
  pins them.
- `folio_dup_swap()`: raises the count when a swap entry replaces the folio,
  as `shmem_writeout()` does.
- Failed memcg charge: `swap_cache_del_folio()` takes the folio out and frees
  the slots; there is no put_swap_folio().
- `mem_cgroup_try_charge_swap()` also runs when no slots were found, to record
  `MEMCG_SWAP_FAIL`.
- `swap_alloc_slow()`: walks the single `swap_avail_head` plist and
  `plist_requeue()`s each device it visits.
- Large folio in `swap_alloc_slow()`: returns after the first device it could
  pin, with or without slots.
- `swap_sync_discard()`: order 0 only, after the local lock is dropped; if it
  discarded anything `folio_alloc_swap()` restarts from the per-CPU cache.
- `cluster_alloc_swap_entry()` returns 0 at once for a large order on a device
  without `SWP_BLKDEV`.
- Cluster order in `cluster_alloc_swap_entry()`:
  1. without `SWP_SOLIDSTATE`: `si->global_cluster->next[order]`
  2. with `SWP_PAGE_DISCARD`: `free_clusters`
  3. if `order < PMD_ORDER`: every cluster on `nonfull_clusters[order]`
  4. without `SWP_PAGE_DISCARD`: `free_clusters`
  5. if `vm_swap_full()`: `swap_reclaim_full_clusters()`, for any order
  6. if `order < PMD_ORDER`: one cluster from `frag_clusters[order]`
  7. order 0 only: `frag_clusters[o]` then `nonfull_clusters[o]` for each
     higher `o`
