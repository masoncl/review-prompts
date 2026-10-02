- `v4l2_subdev_enable_streams_api`: `static bool` in
  `drivers/media/v4l2-core/v4l2-subdev.c`, under
  `CONFIG_VIDEO_V4L2_SUBDEV_API`; nothing assigns it and there is no
  `module_param()` for it, so it is false unless the source is edited.
- Userspace result while it is false: `subdev_do_ioctl()` returns
  `-ENOIOCTLCMD` for both routing ioctls, which `video_usercopy()` in
  `drivers/media/v4l2-core/v4l2-ioctl.c` turns into `-ENOTTY`.
- Three gates on the routing ioctls, in order: the variable
  (`-ENOIOCTLCMD`), `V4L2_SUBDEV_FL_STREAMS` in `sd->flags`
  (`-ENOIOCTLCMD`), `V4L2_SUBDEV_CLIENT_CAP_STREAMS` in the file handle's
  `client_caps` (`-EINVAL`).
- `__v4l2_subdev_init_finalize()`: does not read the variable; in-kernel
  routing, stream configs and `v4l2_subdev_enable_streams()` work with the
  variable false.
- Enforced by the core for a `V4L2_SUBDEV_FL_STREAMS` sub-device: only the
  two `-EINVAL` tests in `__v4l2_subdev_init_finalize()`. A streams
  sub-device with neither `s_stream` nor `enable_streams` passes.
- `set_routing`: optional; without it `VIDIOC_SUBDEV_S_ROUTING` copies the
  current table back and returns 0.
- `init_state`: not checked; without a routing installed there, the state
  has no stream configs and `check_state()` returns `-EINVAL` for every
  pad/stream.
- **Unsafe usage**: calling `v4l2_subdev_enable_streams()` or
  `v4l2_subdev_disable_streams()` on a `V4L2_SUBDEV_FL_STREAMS` sub-device
  that lacks `enable_streams`/`disable_streams`; the state pointer is NULL
  on that path and `v4l2_subdev_collect_streams()` dereferences it.
  - Safe: the sub-device implements both ops and has an active state from
    `v4l2_subdev_init_finalize()`, as `ub913_enable_streams()` and
    `ub913_subdev_init()` in `drivers/media/i2c/ds90ub913.c`; the state is
    then locked and passed.
