- `dma_fence_add_callback()` returning `-EINVAL`: NULL `fence` or NULL
  `func`, with a `WARN_ON()`.
- `cb->node`: initialised on `-ENOENT`, not on `-EINVAL`; only after
  `-ENOENT` or success is a later `dma_fence_remove_callback()` defined.
- `-ENOENT` is also returned when `enable_signaling` returns false during
  this call; the core then signals the fence inside
  `dma_fence_add_callback()`, and callbacks other users installed run in the
  caller's context.
- When a callback runs: the signalled bit is set, `fence->cb_list` is already
  overwritten by `timestamp`, and `fence->ops` may be NULL.
- `cb->node` is re-initialised before `func` is called, so `func` may free or
  reuse the structure that embeds `cb`.
- **Unsafe usage**: from a callback, calling a function that takes the fence
  lock (`dma_fence_remove_callback()`, `dma_fence_signal()`,
  `dma_fence_get_status()`, `dma_fence_enable_signaling()`) on the signalling
  fence, or one of those or `dma_fence_add_callback()` on another fence
  initialised with the same external lock.
  - Safe: queue an `irq_work` and do it there, as `dma_fence_chain_cb()`
    does; `dma_fence_spinlock()` shows which fences share a lock.
- Reference taken in `enable_signaling`: the core never drops it;
  `dma_fence_signal()` puts nothing. The driver's signalling path must drop
  it, as `dma_fence_array_cb_func()` and `irq_dma_fence_array_work()` do for
  the references `dma_fence_array_enable_signaling()` takes.
