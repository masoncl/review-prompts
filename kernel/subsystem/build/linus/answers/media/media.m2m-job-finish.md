- `v4l2_m2m_buf_done_and_job_finish()` order: destination buffer first, unless
  it is held, then the source buffer, then the job; both get the same `state`.
  The reason in the code: completing the source buffer unbinds it from its
  request and may signal the request fd.
- `v4l2_m2m_job_finish()`: does not touch buffers and imposes no order.
- `_v4l2_m2m_job_finish()` for a context that is not `curr_ctx`: returns
  `false` with only a `dprintk()`; no warning, nothing is scheduled.
- Next job: `v4l2_m2m_schedule_next_job()` requeues the same context with
  `__v4l2_m2m_try_queue()` and calls `schedule_work()` on `job_work`; it does
  not call `v4l2_m2m_try_run()` directly.
- Calling either finish function from inside `device_run`: works, because the
  next run is deferred; `cedrus_device_run()` does so on a setup error.
  `include/media/v4l2-mem2mem.h` has no rule against it.
- `v4l2_m2m_job_finish()` on a queue with
  `VB2_V4L2_FL_SUPPORTS_M2M_HOLD_CAPTURE_BUF`: `WARN_ON()` only; the job is
  still finished, but `is_held` is never updated.
- `TRANS_ABORT`: stays set after the job ends, so the context is not requeued
  until `v4l2_m2m_streamoff()` zeroes `job_flags`.
- **Unsafe usage**: calling `v4l2_m2m_buf_done_and_job_finish()` after the
  driver has removed the source or destination buffer from the ready list.
  - Unsafe: with the list then empty it does
    `WARN_ON(!src_buf || !dst_buf)` and returns without finishing the job, so
    `curr_ctx` stays set and `v4l2_m2m_cancel_job()` never wakes; with more
    buffers on the list it completes the next ones instead.
  - Safe: peek with `v4l2_m2m_next_src_buf()` and `v4l2_m2m_next_dst_buf()`
    and let the helper remove them, as `cedrus_device_run()` and
    `hantro_job_finish_no_pm()` do.
  - Safe: remove the buffers yourself and call plain `v4l2_m2m_job_finish()`,
    as `device_work()` in `drivers/media/test-drivers/vim2m.c`.
