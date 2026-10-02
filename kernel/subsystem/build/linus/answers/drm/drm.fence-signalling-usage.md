- **Unsafe usage**: between making a fence visible and signalling it, taking
  a lock that `dma_resv_lockdep()` in `drivers/dma-buf/dma-resv.c` holds when
  it calls `__dma_fence_might_wait()`: `mmap_lock`, any `struct dma_resv`
  lock, or entering reclaim through an allocation.
  - Safe: allocate before the fence is visible and only initialise inside the
    section, as `dma_fence_array_alloc()` followed by
    `dma_fence_array_init()` allows.
  - Safe: an allocation mask without `__GFP_DIRECT_RECLAIM`, with the failure
    handled, as `xe_guc_log_snapshot_alloc()` does with `GFP_ATOMIC` when
    `devcoredump_snapshot()` reaches it inside the section;
    `__need_reclaim()` in `mm/page_alloc.c` defines this.
- Any `struct dma_resv` lock is covered, not only one held across an
  allocation: all share `reservation_ww_class`.
- `GFP_NOFS` and `GFP_NOIO` are forbidden too: under `CONFIG_MMU_NOTIFIER`
  `fs_reclaim_acquire()` takes `__mmu_notifier_invalidate_range_start_map`
  whenever `__need_reclaim()` is true, with or without `__GFP_FS`.
- For a `struct dma_resv`, the section starts at `dma_resv_add_fence()`,
  before `dma_resv_unlock()`: `dma_resv_for_each_fence_unlocked()` reads
  without the lock.
- `dma_fence_begin_signalling()` returns a `bool`: false when it acquired
  `dma_fence_lockdep_map`, true when it did nothing; pass that value to the
  matching `dma_fence_end_signalling()`, which releases only on false.
- `dma_fence_begin_signalling()` does nothing when the section is already
  open or when `in_atomic()` is true, so a section in atomic context is not
  recorded.
- Without `CONFIG_LOCKDEP`, `dma_fence_begin_signalling()`,
  `dma_fence_end_signalling()` and `__dma_fence_might_wait()` are stubs.
- Only `dma_fence_signal()` annotates itself; `dma_fence_signal_timestamp()`,
  `dma_fence_signal_locked()`, `dma_fence_signal_timestamp_locked()`,
  `dma_fence_check_and_signal()` and `dma_fence_check_and_signal_locked()`
  do not.
- Wait side: only `dma_fence_wait_timeout()` calls
  `__dma_fence_might_wait()`; `dma_fence_wait_any_timeout()` and a direct
  `dma_fence_default_wait()` do not.
- A fence wait inside a signalling section is not reported:
  `__dma_fence_might_wait()` drops the section's hold on the map before it
  takes the map; nothing checks for a cycle between fences.
- No file under `drivers/gpu/drm/scheduler/` calls
  `dma_fence_begin_signalling()`; drivers annotate their own paths, for
  example `drivers/gpu/drm/panfrost/panfrost_job.c`.
