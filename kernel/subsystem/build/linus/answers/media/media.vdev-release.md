- `v4l2_device_release()` in `drivers/media/v4l2-core/v4l2-dev.c`: calls
  `vdev->release(vdev)`, then `v4l2_device_put()` last.
- `v4l2_device_put()` there: skipped when `v4l2_dev->release` is NULL, so a
  driver without that callback may free its `struct v4l2_device` from
  `vdev->release`; a driver with it must not.
- No file open and no other reference: `vdev->release` runs inside
  `video_unregister_device()`, from `device_unregister()`; the caller must
  not touch a vdev that its release frees.
- `vb2_video_unregister_device()`: holds its own reference across the
  unregister, so release runs at its final `put_device()` at the earliest.
- `struct v4l2_device` after unregister: `v4l2_release()` and
  `v4l2_device_release()` still read `vdev->v4l2_dev`, `v4l2_dev->mdev` and
  `v4l2_dev->release`; it must outlive the last close.
- `vdev->fops` after unregister: `v4l2_release()` calls
  `vdev->fops->release` on every close, under `mdev->req_queue_mutex` when
  `v4l2_device_supports_requests()` is true.
- **Unsafe usage**: `video_device_release_empty()` on a
  `struct video_device` whose memory is freed at a point not ordered after
  `v4l2_device_release()`, for example in the driver's remove path.
  - Safe: `video_device_release_empty()` with the container freed from
    `v4l2_dev->release`, as `gspca_release()` and `vivid_dev_release()` do;
    `v4l2_device_release()` drops the node's `struct v4l2_device` reference
    only after `vdev->release` returned.
  - Safe: a `vdev->release` that frees the container itself, as
    `v4l2_device_release_subdev_node()` in
    `drivers/media/v4l2-core/v4l2-device.c` does for its own allocation.
