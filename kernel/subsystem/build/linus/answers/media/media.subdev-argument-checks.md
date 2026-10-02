- NULL argument pointer: `-EINVAL` before any other check, in the wrappers
  that call `check_state()`.
- `check_pad()`: bounds by `sd->entity.num_pads` only under
  `CONFIG_MEDIA_CONTROLLER` and when `num_pads` is not 0; otherwise only
  pad 0 passes.
- `check_state()` on a sub-device with `V4L2_SUBDEV_FL_STREAMS`: passes only
  if `v4l2_subdev_state_get_format()` finds an entry for the pad and stream
  in the state. `which` is not consulted.
- NULL state on a sub-device with `V4L2_SUBDEV_FL_STREAMS`:
  `__v4l2_subdev_state_get_format()` hits `WARN_ON_ONCE(!state)` and the
  check returns `-EINVAL`.
- `CONFIG_VIDEO_V4L2_SUBDEV_API` in `check_state()`: matters only inside the
  `V4L2_SUBDEV_FL_STREAMS` branch, where without it every call returns
  `-EINVAL`. It does not affect `V4L2_SUBDEV_FORMAT_TRY` on a sub-device
  without the flag.
- `V4L2_SUBDEV_FORMAT_ACTIVE` without `V4L2_SUBDEV_FL_STREAMS`: a NULL
  state passes `check_state()` when `stream` is 0.
- `v4l2_subdev_enable_streams_api`: not consulted; `check_state()` tests
  `sd->flags` only.
