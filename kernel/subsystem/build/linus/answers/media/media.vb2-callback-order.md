- `buf_out_validate`: called on output queues at the start of every
  `__buf_prepare()` that finds `vb->prepared` clear, with or without requests.
- `buf_out_validate` for a request: `vb2_core_qbuf()` calls it when an
  unprepared buffer is bound to a request, and `vb2_req_prepare()` calls it
  again through `__buf_prepare()` when the request is queued.
- `buf_init` at allocation: MMAP only, in `__vb2_queue_alloc()`. USERPTR and
  DMABUF buffers get it at their first prepare.
- `buf_queue` before `start_streaming`: only for buffers already on
  `queued_list` when `vb2_start_streaming()` runs.
- `min_queued_buffers` of 0 with nothing queued: `start_streaming` is called
  with count 0 and every `buf_queue` comes after it.
- `buf_finish` without a dequeue: `__vb2_queue_cancel()` calls it for every
  buffer with `vb->prepared` set, including one that was only prepared and
  never saw `buf_queue`.
- `prepare_streaming` skipped: `vb2_core_streamon()` returns 0 when already
  streaming, and `-EINVAL` with no buffers or fewer buffers allocated than
  `min_queued_buffers`, before the call.
- `unprepare_streaming` after a failed start: called by `vb2_core_streamon()`;
  not called when the failed `vb2_start_streaming()` came from
  `vb2_core_qbuf()`, where it waits for `__vb2_queue_cancel()`.
- `unprepare_streaming` in `__vb2_queue_cancel()`: runs after `stop_streaming`
  and before the core reclaims buffers the driver still owns.
- Can run with `start_streaming` never called: `buf_init`, `buf_out_validate`,
  `buf_prepare`, `buf_finish`, `buf_cleanup`, `prepare_streaming`,
  `unprepare_streaming`.
- `stop_streaming`: only after a `start_streaming` that returned 0.
