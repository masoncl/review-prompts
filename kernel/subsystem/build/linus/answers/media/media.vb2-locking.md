- `__vb2_wait_for_done_vb()`: calls `mutex_unlock(q->lock)` and
  `mutex_lock(q->lock)` unconditionally; a NULL `lock` never gets this far
  (see "Initialising a queue").
- `struct vb2_ops` has no `wait_prepare` or `wait_finish` member; under
  `drivers/media/` those names exist only in the amphion driver's own
  `struct vpu_inst_ops`. There are no vb2_ops_wait_prepare or
  vb2_ops_wait_finish helpers.
- **Unsafe usage**: a blocking `vb2_core_dqbuf()` or `vb2_dqbuf()` when the
  caller does not hold `q->lock`; the wait unlocks a mutex that is not held.
  - Safe: caller holds `q->lock`, as `vb2_thread()` does around
    `vb2_core_dqbuf()`.
  - Safe: ioctl through `video_ioctl2()` with `vdev->queue` set, or with an
    m2m context; `v4l2_ioctl_get_lock()` then returns that queue's lock.
- `vdev->queue` unset and no m2m context: the ioctl core holds only
  `vdev->lock`, so `q->lock` must be that same mutex, or the handler takes
  `q->lock` itself, as `isp_video_dqbuf()` in
  `drivers/media/platform/ti/omap3isp/ispvideo.c` does.
- `videobuf2-core.c` takes `q->lock` itself only in `vb2_req_prepare()`,
  `vb2_req_unprepare()`, `vb2_req_queue()` and `vb2_thread()`, besides the
  relock in `__vb2_wait_for_done_vb()`; the `vb2_core_` functions and the
  `vb2_ioctl_` helpers rely on the caller.
- `q->lock` is never asserted by the core; `v4l2_m2m_ctx_release()` calls
  `vb2_queue_release()` on both queues and takes no lock, so its caller
  decides what `stop_streaming` runs under.
- `buf_cleanup` from `__vb2_queue_free()`: also under `q->mmap_lock`;
  `buf_cleanup` from `__prepare_userptr()` or `__prepare_dmabuf()` is not.
- `q->waiting_in_dqbuf`: set while the lock is dropped; `vb2_core_reqbufs()`
  with a non-zero count, `vb2_core_create_bufs()` on an empty queue,
  `__vb2_perform_fileio()` and a second waiter return `-EBUSY`.
- STREAMOFF and a queue release still run during the wait; the sleeper then
  returns `-EINVAL` because `q->streaming` is clear.
