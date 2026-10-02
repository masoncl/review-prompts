- `ring_buffer_read_start()`: raises only `cpu_buffer->resize_disabled`;
  writers keep running. It takes a `gfp_t`, and takes `buffer->mutex` around
  the increment when the flags allow blocking.
- `kernel/trace/trace.c` stops the tracer for an iterator only when
  `TRACE_ITER(PAUSE_ON_TRACE)` is set.
- `ring_buffer_read_page()`: holds `reader_lock` with interrupts off from
  before `rb_get_reader_page()` until it returns, the event-by-event copy
  included.
- `ring_buffer_read_page()` on a mapped, persistent or remote buffer
  (`rb_is_static()`), or with a page of another order: copies, never swaps,
  never refuses for that reason.
- `ring_buffer_map_get_reader()`: reports loss in the new reader sub-buffer
  (`RB_MISSED_EVENTS`, plus `RB_MISSED_STORED` and the count when there is
  room), unless that sub-buffer is also the commit page. It zeroes
  `cpu_buffer->lost_events` before `rb_update_meta_page()` copies that field
  to `reader.lost_events`.
- Unknown loss count: a page whose `commit` carries `RB_MISSED_EVENTS` gives
  `lost_events` of -1. `ring_buffer_read_page()` then stores no count and
  does not add `RB_MISSED_STORED`.
- `ring_buffer_iter_dropped()`: boolean only, no count;
  `ring_buffer_iter_advance()` clears it.
- `ring_buffer_peek()`: leaves `cpu_buffer->lost_events` set, so the same
  loss is reported again; `ring_buffer_consume()` and
  `ring_buffer_read_page()` clear it.
- Iterator after a consuming read or a page removal: `rb_iter_peek()` resets
  it silently; `rb_iter_reset()` zeroes `missed_events`.
- `rb_reader_lock()` in NMI: only tries `reader_lock`; on failure reads
  unlocked and raises `cpu_buffer->record_disabled` for good. Only
  `ring_buffer_consume()`, `ring_buffer_peek()`, `ring_buffer_empty()` and
  `ring_buffer_empty_cpu()` use it.
