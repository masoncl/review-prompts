- `ring_buffer_resize()` returns 0 without resizing: for a NULL buffer, a CPU
  not in `buffer->cpumask`, or one CPU already at the size (tested before
  `resize_disabled`).
- `ring_buffer_resize()` with `RING_BUFFER_ALL_CPUS`: one CPU with
  `resize_disabled` set refuses the whole call with -EBUSY.
- Persistent and remote buffers: `rb_allocate_cpu_buffer()` raises
  `resize_disabled` and never drops it, so resize and order change return
  -EBUSY for the life of the buffer.
- `ring_buffer_subbuf_order_set()`: raises `buffer->record_disabled` once,
  then `synchronize_rcu()`; it does not raise `resize_disabled` or the
  per-CPU `record_disabled`.
- `ring_buffer_subbuf_order_set()` -EINVAL: a NULL buffer, `order < 0`,
  `psize <= BUF_PAGE_HDR_SIZE` or `psize > RB_WRITE_MASK + 1`. An unchanged
  order returns 0 before the busy test.
- Splice reader holding a page of the old order: `ring_buffer_read_page()`
  copies on an order mismatch; `ring_buffer_alloc_read_page()` reallocates.
- `buffer_subbuf_size_write()` in `kernel/trace/trace.c`: calls
  `tracing_stop_tr()` and `trace_access_lock()` around the order change.
- `ring_buffer_swap_cpu()`: there is no RB_FL_SNAPSHOT flag here; it does not
  test `resize_disabled` and calls no `synchronize_rcu()`.
- `ring_buffer_swap_cpu()` -EBUSY: `current_context` non-zero on either CPU
  buffer (not `committing`), or `buffer->resizing` set on either buffer.
- `ring_buffer_swap_cpu()` on a `rb_is_static()` buffer: `WARN_ON_ONCE()` and
  -EBUSY; keeping static buffers away is the caller's job.
- `ring_buffer_swap_cpu()` check order: masks (-EINVAL), static (-EBUSY),
  `nr_pages` and `subbuf_order` (-EINVAL), `record_disabled` (-EAGAIN), then
  the -EBUSY tests.
- `ring_buffer_swap_cpu()` caller: recording must be enabled (else -EAGAIN);
  its one caller, `update_max_tr_single()` in
  `kernel/trace/trace_snapshot.c`, asserts that interrupts are off.
- Without `CONFIG_RING_BUFFER_ALLOW_SWAP`: `ring_buffer_swap_cpu()` is a stub
  in `include/linux/ring_buffer.h` that returns -ENODEV.
- `ring_buffer_reset_cpu()` on a mapped buffer: resets and refreshes the meta
  page through `rb_update_meta_page()`.
- `reset_disabled_cpu_buffer()`: if `committing` is still non-zero it skips
  the reset, and `RB_WARN_ON()` leaves `buffer->record_disabled` raised.
- `rb_reset_cpu()` on a remote buffer: calls `remote->reset`; does nothing
  when that callback is NULL.
