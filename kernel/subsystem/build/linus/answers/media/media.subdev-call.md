- `sd->ops` NULL: not tested; `v4l2_subdev_call()` dereferences `__sd->ops`.
  `v4l2_subdev_init()` in `drivers/media/v4l2-core/v4l2-subdev.c` does
  `BUG_ON(!ops)`.
- `CONFIG_MEDIA_CONTROLLER`: changes nothing in `v4l2_subdev_call()`; the
  macro takes no module or entity reference.
- NULL `sd` in the sibling macros: only `v4l2_subdev_call()` tolerates it.
  `v4l2_subdev_call_state_active()` reads `sd->active_state` and
  `v4l2_subdev_call_state_try()` reads `sd->state_lock` before the NULL test
  runs; `v4l2_subdev_has_op()` dereferences `sd` too.
- `-ENOIOCTLCMD` returned from an ioctl handler: `video_usercopy()` in
  `drivers/media/v4l2-core/v4l2-ioctl.c` turns it into `-ENOTTY`, so
  `subdev_do_ioctl()` can return the result of `v4l2_subdev_call()`
  unchanged, as it does for example for `VIDIOC_SUBDEV_G_FMT`.
- `-ENOIOCTLCMD` on any other path (probe, streaming start, notifier):
  `v4l2_subdev_call()` does not convert it; the caller filters or maps it, as
  `v4l2_get_link_freq()` does with `ret < 0 && ret != -ENOIOCTLCMD`.
- `-ENOIOCTLCMD` does not prove that the operation is missing: an implemented
  operation can return the same code, for example
  `v4l2_subdev_s_stream_helper()` returns `-ENOIOCTLCMD`.
