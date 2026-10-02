- `__prepare_dmabuf()`: compares the plane `length` (from user space, or
  `dbuf->size` when 0) with `min_length`; `data_offset` plays no part.
- Real dma-buf size: checked against `length` by the `attach_dmabuf` memop of
  each allocator in `drivers/media/common/videobuf2/`, which returns
  `-EFAULT`, for each plane it attaches.
- `__prepare_userptr()`: skips the `min_length` test for a plane whose pointer
  and length are unchanged; `__prepare_dmabuf()` tests every plane each time.
- Same memory queued again: `buf_prepare` still runs; only `buf_cleanup` and
  `buf_init` are skipped.
- `buf_prepare` fails on an imported buffer: the core calls `buf_cleanup` and
  releases every plane, so the next prepare calls `buf_init` again.
- `buf_init` fails: planes are released with no `buf_cleanup`.
- MMAP `buf_prepare` failure: no `buf_cleanup`, memory kept.
- USERPTR change: only the changed planes are released and pinned again.
- DMABUF change in any plane: all planes are detached and attached again.
- `buf_cleanup` and `buf_init` run once per buffer per reacquire, not once
  per plane.
- `__vb2_queue_free()`: skips `buf_cleanup` when `planes[0].mem_priv` is NULL,
  which is the case for an imported buffer never prepared or whose last
  `__prepare_userptr()` or `__prepare_dmabuf()` failed.
- Core checks nothing against the current format; `__verify_length()` in
  `videobuf2-v4l2.c` covers output queues only.
