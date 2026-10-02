- Without `SHRINKER_NUMA_AWARE`: `sc->nid` is still the node being reclaimed.
  `do_shrink_slab()` never writes it; only the `nr_deferred` index is forced
  to 0, in `xchg_nr_deferred()` and `add_nr_deferred()`.
- Kerneldoc of `shrink_slab()`: says unaware shrinkers receive node 0; the code
  does not do that.
- Without `SHRINKER_NUMA_AWARE`: `shrink_slab()` does not skip the shrinker for
  any node, so `drop_slab()` calls it for each online node.
- Without `SHRINKER_MEMCG_AWARE`: `sc->memcg` is whatever `shrink_slab()` was
  given. That is `root_mem_cgroup` when memcg is enabled, and NULL only when
  memcg is disabled or without `CONFIG_MEMCG`.
- `shrinker_alloc()` clears `SHRINKER_MEMCG_AWARE` when `shrinker_memcg_alloc()`
  returns `-ENOSYS`: without `CONFIG_MEMCG`, when `mem_cgroup_disabled()`, or
  when `mem_cgroup_kmem_disabled()` and `SHRINKER_NONSLAB` is not set.
- `shrinker->nr_deferred`: not allocated while `SHRINKER_MEMCG_AWARE` is kept.
  The root pass uses the `struct shrinker_info` of `sc->memcg` too.
- `set_shrinker_bit()`: outside `mm/shrinker.c`, its callers are
  `__list_lru_add()` and `memcg_reparent_list_lru_one()` in `mm/list_lru.c`.
- `__list_lru_init()`: copies `shrinker->id` into the `shrinker_id` field of
  `struct list_lru`, so `shrinker_alloc()` must come before
  `list_lru_init_memcg()`.
- `list_lru_init()`: stores -1 as the id; `set_shrinker_bit()` ignores a
  negative id, so adding to that list sets no memcg bit.
- **Potentially unsafe usage**: a callback under a `SHRINKER_MEMCG_AWARE`
  shrinker that counts state not split by memcg.
  - Unsafe: when it returns the whole count for a non-root `sc->memcg`; the
    same objects are then counted once for every memcg whose bit is set.
  - Safe: return 0 unless `mem_cgroup_shrink_is_root()` is true, as
    `btrfs_nr_cached_objects()` and `shmem_unused_huge_count()` do under
    `super_cache_count()`.
- `shrinker_debugfs_count_show()`: passes NULL as `sc->memcg` to a
  non-memcg-aware shrinker, and calls a non-NUMA-aware one for node 0 only.
- `shrinker_debugfs_scan_write()`: passes the node the user wrote, without
  testing `SHRINKER_NUMA_AWARE`.
