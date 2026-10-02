- `dma_resv_usage_rw()`: gives the level to query or wait on, not the level
  to add at; a writer adds at `DMA_RESV_USAGE_WRITE` and waits on
  `dma_resv_usage_rw(true)`, which is `DMA_RESV_USAGE_READ`. Compare
  `dma_buf_import_sync_file()` and `dma_buf_export_sync_file()` in
  `drivers/dma-buf/dma-buf.c`.
- `dma_resv_reserve_fences()`: returns `-ENOMEM` when it cannot allocate.
- `dma_resv_reserve_fences()` with `num_fences` 0: `WARN_ON()` and
  `-EINVAL`.
- `dma_resv_add_fence()` with no free slot: `BUG_ON()`; on an object that
  never had `dma_resv_reserve_fences()` called, it dereferences a NULL list.
- Reserved slots after `dma_resv_unlock()`: dropped only under
  `CONFIG_DEBUG_MUTEXES`, by `dma_resv_reset_max_fences()`; code must reserve
  again after every relock to pass that check.
- `dma_resv_add_fence()` reuses a slot instead of taking a new one when the
  old fence has signalled, or when it has the same context, the new fence is
  later or the same, and the old usage is equal or weaker (`old_usage >=
  usage`).
- Same context with a weaker new usage: no replacement; both fences stay and
  a reserved slot is consumed.
