- `lock`: mandatory; `vb2_core_queue_init()` returns `-EINVAL` with `WARN_ON`
  when it is NULL.
- `lock` must be the mutex the callers of the queue hold; see "Locks around
  queue operations".
- `max_num_buffers` above `MAX_BUFFER_INDEX`: clamped, not refused.
- `max_num_buffers` below `VB2_MAX_FRAME` (after 0 was replaced): refused.
- `min_reqbufs_allocation` above `max_num_buffers`: refused, tested after it
  was raised to `min_queued_buffers + 1`.
- Not tested at init: `io_modes` against `mem_ops`. `vb2_verify_memory_type()`
  returns `-EINVAL` at REQBUFS or CREATE_BUFS time.
- Init uses `WARN_ON` and `-EINVAL` only; `BUILD_BUG_ON()` in
  `vb2_queue_init_name()` covers the memory enum values.
- `vb2_queue_init_name()` with a NULL name: clears `q->name`, and the core
  then generates one.
