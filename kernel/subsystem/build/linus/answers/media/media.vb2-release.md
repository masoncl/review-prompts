- `vb2_fop_release()`: takes `vdev->queue->lock`, and `vdev->lock` only if
  that is NULL.
- `_vb2_fop_release()`: calls `vb2_queue_release()` when `owner` is NULL or is
  the closing file.
- The queue release in `vb2_video_unregister_device()` is unconditional; it
  does not depend on streaming or on there being an owner.
- `vb2_video_unregister_device()` on a device that is not registered: returns
  at once and does not release the queue.
- Close after `vb2_video_unregister_device()`: `owner` is NULL, so
  `_vb2_fop_release()` calls `vb2_queue_release()` again; on the empty queue
  no driver operation runs.
- `video_unregister_device()` alone: does not touch `vdev->queue`; with
  `vb2_fop_release()` as the release op, `stop_streaming` then runs at the
  owner's close.
- `vb2_video_unregister_device()` takes the queue lock itself, so the caller
  must not hold it.
- **Potentially unsafe usage**: freeing the structure that holds the
  `struct vb2_queue` and its mutex.
  - Unsafe: in the remove function while a file is open; the later
    `vb2_fop_release()` reads `vdev->queue->lock` and locks it.
  - Safe: in the `release` callback of `struct video_device`, which
    `v4l2_device_release()` calls after the last close, as
    `video_i2c_release()` in `drivers/media/i2c/video-i2c.c` does.
