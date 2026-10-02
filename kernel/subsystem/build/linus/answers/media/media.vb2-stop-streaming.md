- Paths that can reach the call: `vb2_core_streamoff()` and
  `vb2_core_queue_release()`, the latter also through `__vb2_cleanup_fileio()`.
- `vb2_core_reqbufs()`: runs `__vb2_queue_cancel()` but returns `-EBUSY` first
  when `q->streaming` is set, so `stop_streaming` is not called from there.
- `vb2_core_create_bufs()`: has no `q->streaming` test and never cancels.
- State passed to `vb2_buffer_done()` in `stop_streaming`: never reaches user
  space; `__vb2_queue_cancel()` empties `done_list` and sets every buffer to
  `VB2_BUF_STATE_DEQUEUED`.
- `__vb2_queue_cancel()` re-initialises `done_list` without `q->done_lock`,
  and `vb2_core_queue_release()` frees the buffers right after.
- **Unsafe usage**: returning from `stop_streaming` while an interrupt
  handler, thread or work item can still call `vb2_buffer_done()`.
  - Safe: stop the producer first, then return the buffers, as
    `vimc_capture_stop_streaming()` does: `vimc_streamer_s_stream()` calls
    `kthread_stop()` before `vimc_capture_return_all_buffers()`.
