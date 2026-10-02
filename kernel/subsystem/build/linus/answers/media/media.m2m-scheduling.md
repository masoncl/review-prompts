- `TRANS_RUNNING`: not tested by `__v4l2_m2m_try_queue()`; a running context is
  skipped because `TRANS_QUEUED` stays set until `_v4l2_m2m_job_finish()`.
- CAPTURE streaming: not required when `m2m_ctx->ignore_cap_streaming` is set;
  OUTPUT streaming is always required. Both are tested before `job_spinlock`
  is taken.
- Ready buffers: the list is `rdy_queue`; `out_q_ctx.buffered` waives the
  source buffer, `cap_q_ctx.buffered` the destination buffer.
- Held capture buffer (`is_held`) whose copied timestamp differs from the
  source's: `__v4l2_m2m_try_queue()` completes it as `VB2_BUF_STATE_DONE`
  itself and tests the next destination buffer; none left means no job,
  unless `cap_q_ctx.buffered` is set.
- `has_stopped`: blocks queueing; tested after the held-buffer step and before
  `job_ready`.
- `QUEUE_PAUSED` in `job_queue_flags`: `v4l2_m2m_try_run()` runs nothing while
  it is set.
- `job_ready`: called under `job_spinlock` with interrupts off, and also from
  the job-finish path, so possibly in hard-IRQ context.
- `device_run`: called in process context, with no m2m spinlock held, from
  three places:

| Caller of `v4l2_m2m_try_run()` | Mutex held |
|---|---|
| `v4l2_m2m_try_schedule()` | whatever its caller holds |
| `v4l2_m2m_device_run_work()` (`job_work`) | none |
| `v4l2_m2m_resume()` | whatever its caller holds |

- `v4l2_m2m_try_run()` runs the head of `job_queue`, which need not be the
  context passed to `v4l2_m2m_try_schedule()`; a mutex held by the caller may
  belong to another context.
- **Unsafe usage**: calling `v4l2_m2m_try_schedule()` from hard-IRQ or atomic
  context, or under a spinlock.
  - Unsafe: it calls `device_run` synchronously, and `device_run` may sleep;
    for example `venus_helper_m2m_device_run()` takes a mutex.
  - Safe: from an ioctl handler, as `v4l2_m2m_qbuf()` does.
  - Safe: from a threaded interrupt handler, as
    `wave5_vpu_dec_finish_decode()` does under `wave5_vpu_irq_thread()`.
  - Safe: from atomic context call `v4l2_m2m_job_finish()` instead;
    `v4l2_m2m_schedule_next_job()` defers the run with `schedule_work()`.
