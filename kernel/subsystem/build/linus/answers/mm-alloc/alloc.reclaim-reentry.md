- There is no __need_fs_reclaim() here; `__need_reclaim()` in
  `mm/page_alloc.c` tests `__GFP_DIRECT_RECLAIM`, `PF_MEMALLOC` and
  `__GFP_NOLOCKDEP`.
- `__GFP_FS`: tested in `fs_reclaim_acquire()` itself, after
  `current_gfp_context()`, and gates only `__fs_reclaim_map`.
- `__mmu_notifier_invalidate_range_start_map`: under `CONFIG_MMU_NOTIFIER`,
  `fs_reclaim_acquire()` acquires and releases it for every mask that passes
  `__need_reclaim()`, including `GFP_NOFS` and `GFP_NOIO`.
- `might_alloc()`: returns before `might_sleep_if()` when the task has
  `PF_MEMALLOC`.
- `__kmalloc_nolock_noprof()`: does not call `slab_pre_alloc_hook()`, so slab
  makes no `might_alloc()` call for it.
- Reclaim-side holders of `__fs_reclaim_map`:
  - `balance_pgdat()`: unconditionally, through `__fs_reclaim_acquire()`.
  - `__perform_reclaim()`, `__alloc_pages_direct_compact()`,
    `__node_reclaim()`, `shrink_all_memory()`: through
    `fs_reclaim_acquire()`, so only when the mask has `__GFP_FS`.
- Lockdep blind spot: an allocation whose effective mask lacks `__GFP_FS`
  never acquires `__fs_reclaim_map`, so a lock that reclaim takes whatever
  the mask is, outside an mmu notifier callback, gets no `might_alloc()`
  report under `GFP_NOFS` or `GFP_NOIO`.
- Priming: code teaches lockdep "reclaim takes L" at init by taking L between
  `fs_reclaim_acquire(GFP_KERNEL)` and `fs_reclaim_release(GFP_KERNEL)`, as
  `dma_resv_lockdep()` in `drivers/dma-buf/dma-resv.c` does.
- **Potentially unsafe usage**: relying on `GFP_NOFS` or
  `memalloc_nofs_save()` to keep reclaim away from a held lock.
  - Unsafe: when the reclaim code that takes the lock does not test
    `sc->gfp_mask`; direct reclaim still runs and still calls it.
  - Safe: when that code returns early without `__GFP_FS`, as
    `super_cache_scan()` in `fs/super.c` does.
  - Safe: when the mask lacks `__GFP_DIRECT_RECLAIM` or the task has
    `PF_MEMALLOC`; `__alloc_pages_slowpath()` then does not enter direct
    reclaim.
