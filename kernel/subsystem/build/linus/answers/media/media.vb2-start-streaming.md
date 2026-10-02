- Failed start: `stop_streaming` and `__vb2_queue_cancel()` are not called;
  `vb2_start_streaming()` reclaims by itself.
- No error code is special; any non-zero return is handled the same way.
- Failure from `vb2_core_streamon()`: the core calls `unprepare_streaming`,
  so `start_streaming` undoes only its own work; `q->streaming` stays 0.
- Failure from `vb2_core_qbuf()`: `q->streaming` stays 1,
  `unprepare_streaming` is not called, and the next QBUF that satisfies
  `min_queued_buffers` calls `vb2_start_streaming()` again.
- After a failure the buffers stay on `queued_list`, except the one whose
  QBUF triggered the start; the next `vb2_start_streaming()` passes each of
  them to `buf_queue` again.
- **Unsafe usage**: a failing `start_streaming` that leaves buffers on the
  driver's own list; the core takes them back and later hands them to
  `buf_queue` a second time.
  - Safe: remove each buffer from the driver list and return it with
    `VB2_BUF_STATE_QUEUED`, as `vid_cap_start_streaming()` in
    `drivers/media/test-drivers/vivid/vivid-vid-cap.c` does.
- **Unsafe usage**: a failing `start_streaming` that returns buffers with
  `VB2_BUF_STATE_DONE` or `VB2_BUF_STATE_ERROR`; the core only does
  `WARN_ON(!list_empty(&q->done_list))` and leaves them on `done_list` while
  they are still on `queued_list`.
  - Safe: `VB2_BUF_STATE_QUEUED`, as `vimc_capture_start_streaming()` does
    through `vimc_capture_return_all_buffers()`.
