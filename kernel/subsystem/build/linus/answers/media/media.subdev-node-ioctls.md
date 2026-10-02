- `vdev->lock`: `__v4l2_device_register_subdev_nodes()` in
  `drivers/media/v4l2-core/v4l2-device.c` allocates the
  `struct video_device` zeroed and never sets `lock`, so for a node the core
  creates only the state lock is taken.
- Order in `subdev_do_ioctl_lock()`: `vdev->lock` if set (interruptible),
  then the state lock with `v4l2_subdev_lock_state()` (not interruptible),
  only if the state is non-NULL.
- Try state: `subdev_fh->state` in `struct v4l2_subdev_fh`, allocated in
  `subdev_open()`; there is no `state` member in `struct v4l2_fh`.
- `which` other than `V4L2_SUBDEV_FORMAT_TRY`: any value selects the active
  state in `subdev_ioctl_get_state()`; `check_which()` rejects a bad value
  later, in the wrapper (not for the routing ioctls, which have none).
- `v4l2_subdev_enable_streams_api`: a `static bool` in
  `drivers/media/v4l2-core/v4l2-subdev.c` that nothing assigns.
  `VIDIOC_SUBDEV_S_CLIENT_CAP` therefore strips
  `V4L2_SUBDEV_CLIENT_CAP_STREAMS`, and `subdev_do_ioctl()` zeroes `stream`
  for every client.
- `VIDIOC_SUBDEV_G_ROUTING`: never calls the driver; it copies from the
  state with `v4l2_subdev_copy_routes()`.
