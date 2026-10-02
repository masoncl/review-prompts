- `struct dma_fence` has no member named lock: it holds an anonymous union
  of `extern_lock` (`spinlock_t *`) and `inline_lock` (`spinlock_t`);
  `DMA_FENCE_FLAG_INLINE_LOCK_BIT` in `flags` says which one is valid.
- `dma_fence_spinlock()` in `include/linux/dma-fence.h` returns the right
  lock; `dma_fence_lock_irqsave()`, `dma_fence_unlock_irqrestore()` and
  `dma_fence_assert_held()` wrap it.
- Kerneldoc in `include/linux/dma-fence.h` and `drivers/dma-buf/dma-fence.c`
  still writes `&dma_fence.lock`; it means the lock `dma_fence_spinlock()`
  returns.
- `lock` argument NULL to `dma_fence_init()` or `dma_fence_init64()`:
  `__dma_fence_init()` initialises `inline_lock` and sets
  `DMA_FENCE_FLAG_INLINE_LOCK_BIT`.
- `ops` NULL, or `ops` without `get_driver_name` or `get_timeline_name`:
  `BUG_ON()` in `__dma_fence_init()`.
- Non-NULL `lock`: its memory must stay valid until the last reference to the
  fence is dropped, not only until the fence signals; the core locks signalled
  fences too, for example in `dma_fence_remove_callback()` and
  `dma_fence_get_status()`.
- **Potentially unsafe usage**: reading `fence->extern_lock` directly.
  - Unsafe: on a fence initialised with a NULL lock; the union then holds the
    spinlock itself, so the value read is not a pointer.
  - Safe: where every fence of that ops table is initialised with a non-NULL
    lock, as `dma_fence_parent()` in `drivers/dma-buf/sync_debug.h` relies on;
    `dma_fence_spinlock()` defines which member is valid.
- Inline locks all share one lockdep class, from the `spin_lock_init()` in
  `__dma_fence_init()`; code that holds one fence's lock while taking another
  fence's lock needs its own class, as `dma_fence_array_init()` and
  `dma_fence_chain_init()` set with `lockdep_set_class()`.
- `seqno` is stored as `u64` by both init functions; only the comparison in
  `__dma_fence_is_later()` differs.
