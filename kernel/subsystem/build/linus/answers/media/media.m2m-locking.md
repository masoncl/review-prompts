- NULL `lock`: `vb2_core_queue_init()` does `WARN_ON(!q->lock)` and returns
  `-EINVAL`, so a `queue_init` that returns the result of `vb2_queue_init()`
  fails when a `lock` is NULL. The "optional" comment on `q_lock` in
  `include/media/v4l2-mem2mem.h` does not match that.
- Different locks: `v4l2_m2m_ctx_init()` does
  `WARN_ON(out_q_ctx->q.lock != cap_q_ctx->q.lock)` and returns
  `ERR_PTR(-EINVAL)`.
- `VIDIOC_ENCODER_CMD` and `VIDIOC_DECODER_CMD`: not `INFO_FL_QUEUE`, so they
  run under `vdev->lock`; the stop helpers take no mutex themselves, while
  `v4l2_m2m_qbuf()` reads the same draining state under `q_lock`.
- `job_spinlock`: not available to drivers; `struct v4l2_m2m_dev` is defined
  in `drivers/media/v4l2-core/v4l2-mem2mem.c`.
- **Unsafe usage**: taking the queue mutex in `device_run`, in `job_abort`, or
  on the path that finishes the job.
  - Unsafe: the dispatcher holds `q_lock` across `v4l2_m2m_qbuf()` and
    `v4l2_m2m_streamon()`, which call `device_run` synchronously, and across
    `v4l2_m2m_streamoff()`, where `v4l2_m2m_cancel_job()` calls `job_abort`
    and then sleeps until `TRANS_RUNNING` clears.
  - Safe: a mutex that is not the queue lock, as `mxc_isi_m2m_device_run()`
    takes `m2m->lock` while its queues use `ctx->vb2_lock`.
  - Safe: no mutex on the completion path, as `device_work()` in
    `drivers/media/test-drivers/vim2m.c`.
