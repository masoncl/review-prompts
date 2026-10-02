- `dma_resv_for_each_fence()`: returns signalled fences too; it filters by
  usage only, see `dma_resv_iter_next()`.
- `dma_resv_for_each_fence_unlocked()`: skips signalled fences, see
  `dma_resv_iter_walk_unlocked()`.
- Unlocked restart: happens only when `obj->fences` points to another list
  (after `dma_resv_reserve_fences()` reallocates or `dma_resv_copy_fences()`
  replaces it) or when `dma_fence_get_rcu()` fails on an entry.
- A fence that `dma_resv_add_fence()` writes into an already reserved slot
  during an unlocked walk: no restart, and the walk may miss it; the result is
  not a snapshot.
- `dma_resv_iter_is_restarted()`: true for the first fence of every walk,
  locked or unlocked; `dma_resv_get_fences()` uses that branch to allocate as
  well as to reset.
- Unlocked loop body: runs with a reference on the current fence and without
  the RCU read lock, which is held only inside
  `dma_resv_iter_first_unlocked()` and `dma_resv_iter_next_unlocked()`; the
  body may sleep, as in `dma_resv_wait_timeout()`.
- `dma_resv_describe()`: uses the locked iterator, so it needs the lock held,
  and it lists fences up to `DMA_RESV_USAGE_READ` only.
