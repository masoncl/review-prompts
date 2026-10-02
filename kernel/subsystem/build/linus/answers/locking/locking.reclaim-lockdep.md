- Map name: `__fs_reclaim_map` in `mm/page_alloc.c`; the class is printed as
  "fs_reclaim".
- `__need_reclaim()`: returns false without `__GFP_DIRECT_RECLAIM`, with
  `PF_MEMALLOC` set on the task, or with `__GFP_NOLOCKDEP`; nothing is
  recorded then.
- `__GFP_IO`: never tested by `fs_reclaim_acquire()`; there is no lockdep map
  for I/O.
- `memalloc_noio_save()`: has the same effect on lockdep as
  `memalloc_nofs_save()`, because `current_gfp_context()` strips `__GFP_FS`
  for both.
- `__mmu_notifier_invalidate_range_start_map`: with `CONFIG_MMU_NOTIFIER`,
  `fs_reclaim_acquire()` acquires and releases it for every allocation that
  passes `__need_reclaim()`, with or without `__GFP_FS`.
- `GFP_NOFS`, `GFP_NOIO` and the nofs and noio scopes: still record "held
  locks -> MMU notifier map"; they skip only `__fs_reclaim_map`.
- kswapd: `balance_pgdat()` calls `__fs_reclaim_acquire()` with no flag test.
- Direct reclaim and direct compaction: `__perform_reclaim()` and
  `__alloc_pages_direct_compact()` call `fs_reclaim_acquire(gfp_mask)`, so
  they hold the map only for an allocation with `__GFP_FS`.
- `fs_reclaim_acquire()` and `fs_reclaim_release()`: each re-reads the task
  flags, so `PF_MEMALLOC` or a nofs scope must not change between the two;
  `__perform_reclaim()` sets `PF_MEMALLOC` after the acquire and clears it
  before the release.
