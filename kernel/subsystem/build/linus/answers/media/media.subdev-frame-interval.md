- `struct v4l2_subdev_video_ops`: has no frame interval member; there are no
  g_frame_interval or s_frame_interval ops in this tree.
- `call_get_frame_interval()` and `call_set_frame_interval()`: only run
  `check_frame_interval()`; they never write `which` and never replace a
  NULL state (see "Operation wrappers").
- Ioctl path: `subdev_ioctl_get_state()` overwrites `fi->which` with
  `V4L2_SUBDEV_FORMAT_ACTIVE` when the file handle lacks
  `V4L2_SUBDEV_CLIENT_CAP_INTERVAL_USES_WHICH`, before it picks the state,
  so the state and the driver both see the forced value.
- `V4L2_SUBDEV_CLIENT_CAP_INTERVAL_USES_WHICH`: accepted by
  `VIDIOC_SUBDEV_S_CLIENT_CAP` regardless of
  `v4l2_subdev_enable_streams_api`.
- `v4l2_g_parm_cap()` and `v4l2_s_parm_cap()` in
  `drivers/media/v4l2-core/v4l2-common.c`: call through
  `v4l2_subdev_call_state_active()`, which passes the active state locked,
  or NULL when the sub-device has none.
- **Unsafe usage**: an in-kernel call of `get_frame_interval` or
  `set_frame_interval` with `which` left at 0. 0 is
  `V4L2_SUBDEV_FORMAT_TRY`; on a sub-device without `V4L2_SUBDEV_FL_STREAMS`
  `check_state()` returns `-EINVAL` for it when the state is NULL or has no
  `pads`, and drivers such as `ov7670_get_frame_interval()` return `-EINVAL`
  for anything but `V4L2_SUBDEV_FORMAT_ACTIVE`.
  - Safe: set `which` to `V4L2_SUBDEV_FORMAT_ACTIVE` before the call, as
    `subdev_ioctl_get_state()` does for a client without the capability.
