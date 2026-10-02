- `v4l2_subdev_call_wrappers`: a `struct v4l2_subdev_ops` with only `.pad`
  and `.video` set; the members are in `v4l2_subdev_call_pad_wrappers` and
  `v4l2_subdev_call_video_wrappers`.
- Easy to miss in the pad table: `s_dv_timings`, `g_dv_timings` and
  `query_dv_timings` are wrapped; `set_routing`, `enable_streams`,
  `disable_streams`, `set_frame_desc` and `link_validate` are not.
- `DEFINE_STATE_WRAPPER`: instantiated for seven operations (formats,
  selections, the three enumerations). `get_frame_interval` and
  `set_frame_interval` are installed as `call_get_frame_interval()` and
  `call_set_frame_interval()`, so a NULL state stays NULL for them.
- State lock: the state wrapper locks only when the caller passed NULL and
  `sd->active_state` exists. With a non-NULL state it does not lock; the lock
  is asserted only for a sub-device with `V4L2_SUBDEV_FL_STREAMS`, by
  `__v4l2_subdev_state_get_format()` under `check_state()`.
- NULL state, no active state: the driver receives NULL; `check_state()`
  lets it through for `V4L2_SUBDEV_FORMAT_ACTIVE` and `stream` 0 on a
  sub-device without `V4L2_SUBDEV_FL_STREAMS`.
- Without `CONFIG_MEDIA_CONTROLLER`: the state wrapper only forwards, so a
  NULL state is not replaced.
- `call_s_stream()` on a failed stop: logs, returns 0, and still clears
  `sd->s_stream_enabled` and the privacy LED.
- `call_get_frame_desc()`: returns `-EOPNOTSUPP` for a pad without
  `MEDIA_PAD_FL_SOURCE` under `CONFIG_MEDIA_CONTROLLER`. It does not call
  `check_pad()`; it indexes `sd->entity.pads[pad]` with the caller's value.
- `call_get_mbus_config()`: zeroes `*config` before `check_pad()`. When the
  operation is missing the wrapper does not run and nothing is zeroed.
- **Unsafe usage**: under `CONFIG_MEDIA_CONTROLLER`, passing a NULL state to
  one of the seven state-wrapped operations while holding the lock of the
  active state of that sub-device; the wrapper calls `mutex_lock()` on it
  again. With `sd->state_lock` set, `__v4l2_subdev_state_alloc()` gives every
  state of the sub-device that one lock, so a locked try state is the same
  case.
  - Safe: pass the state that is already locked, as
    `v4l2_subdev_link_validate_get_format()` does with
    `v4l2_subdev_get_locked_active_state()` when `states_locked` is true; the
    wrapper calls `v4l2_subdev_lock_and_get_active_state()` only for a NULL
    state.
