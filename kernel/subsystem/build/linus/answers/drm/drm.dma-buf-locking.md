- There is no dma_buf_move_notify() and no move_notify member here; the
  exporter calls `dma_buf_invalidate_mappings()` with the reservation lock
  held (asserted), and the importer supplies `invalidate_mappings` in
  `struct dma_buf_attach_ops`.
- Driver functions keep the old word in their names, for example
  `amdgpu_dma_buf_move_notify()` is installed as `.invalidate_mappings`.
- There is no CONFIG_DMABUF_MOVE_NOTIFY; `dma_buf_pin_on_map()` is true when
  the exporter has a `pin` op and the attachment has no `importer_ops`.
- Dynamic means `importer_ops` is non-NULL, even when `invalidate_mappings`
  is NULL; `dma_buf_attach_revocable()` tests for the callback itself.
- `dma_buf_attachment_is_dynamic()` is `static` in
  `drivers/dma-buf/dma-buf.c`; drivers cannot call it.
- Lock rule for `dma_buf_map_attachment()`, `dma_buf_unmap_attachment()`,
  `dma_buf_vmap()` and `dma_buf_vunmap()`: applies to every importer, dynamic
  or not; each asserts the lock unconditionally.
- `dma_buf_pin()` and `dma_buf_unpin()`: `WARN_ON()` for a non-dynamic
  attachment.
- Non-dynamic importer: the core calls the exporter's `pin` in
  `dma_buf_map_attachment()` and `unpin` in `dma_buf_unmap_attachment()`, not
  at attach time; the `pin` kerneldoc in `include/linux/dma-buf.h` says
  otherwise.
- The core caches no sg_table: `struct dma_buf_attachment` has no member for
  one, and each map call reaches `map_dma_buf`.
- Non-dynamic importer: `dma_buf_map_attachment()` waits interruptibly for the
  `DMA_RESV_USAGE_KERNEL` fences before it returns; a dynamic importer gets no
  wait and must wait itself.
- `dma_buf_dynamic_attach()` and `dma_buf_detach()`: take the lock only around
  the attachment list update; the exporter's `attach` and `detach` run outside
  it.
- `dma_buf_begin_cpu_access()` and `dma_buf_end_cpu_access()`: only
  `might_lock()` the reservation lock; they do not take it.
