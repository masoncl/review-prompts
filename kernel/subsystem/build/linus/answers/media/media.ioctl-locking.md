- `v4l2_ioctl_get_lock()` and the locking: both in
  `drivers/media/v4l2-core/v4l2-ioctl.c`; `__video_do_ioctl()` locks and
  unlocks. `v4l2_ioctl()` in `drivers/media/v4l2-core/v4l2-dev.c` takes no
  lock.
- Both mutexes that `__video_do_ioctl()` takes, `req_queue_mutex` and the
  lock from `v4l2_ioctl_get_lock()`: taken with
  `mutex_lock_interruptible()`; a signal gives `-ERESTARTSYS`.
- `req_queue_mutex` of `struct media_device`: taken first, for
  `VIDIOC_STREAMON`, `VIDIOC_STREAMOFF` and `VIDIOC_REQBUFS`, when
  `v4l2_device_supports_requests()` is true. The lock from
  `v4l2_ioctl_get_lock()` is taken second; unlock is in reverse order.
- Order of tests in `v4l2_ioctl_get_lock()`:
  1. `_IOC_NR(cmd) >= V4L2_IOCTLS` (private or unknown number): `vdev->lock`.
  2. `INFO_FL_QUEUE` ioctl and `vfh->m2m_ctx->q_lock` set: that lock.
  3. `INFO_FL_QUEUE` ioctl and `vdev->queue->lock` set: that lock.
  4. Otherwise `vdev->lock`.
- `INFO_FL_QUEUE` ioctls: search the `v4l2_ioctls` table for the flag;
  `VIDIOC_REMOVE_BUFS` is one of them.
- `m2m_ctx->q_lock`: `v4l2_m2m_ctx_init()` sets it to the output queue's
  lock and fails with `-EINVAL` if the capture queue uses another mutex.
- No per-ioctl opt-out: `struct video_device` has no `disable_locking`
  member, and there is no v4l2_disable_ioctl_locking() or
  V4L2_FL_LOCK_ALL_FOPS. An ioctl runs with no core lock only when the
  pointer chosen above is NULL and `req_queue_mutex` is not taken.
- Other file operations in `v4l2-dev.c`: `v4l2_release()` holds
  `req_queue_mutex` around the driver's `release` when requests are
  supported; the others hold no lock around the driver op. `vb2_fop_mmap()`
  takes neither `q->lock` nor `vdev->lock`.
- Sub-device nodes: `subdev_do_ioctl_lock()` in
  `drivers/media/v4l2-core/v4l2-subdev.c` takes `vdev->lock` if set, then
  the state lock, if the state is non-NULL, for the ioctls listed in
  `subdev_ioctl_get_state()`. It never takes `req_queue_mutex`.
