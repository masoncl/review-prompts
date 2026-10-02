- `call_s_stream()`: makes no test that the op exists;
  `v4l2_subdev_call()` returns `-ENOIOCTLCMD` for a missing op and
  `-ENODEV` for a NULL sub-device before the wrapper runs.
- `call_s_stream()` on a redundant start or a redundant stop: `WARN_ON()`
  and return 0; the driver is not called.
- `call_s_stream()`: takes no lock; only the callers serialise
  `sd->s_stream_enabled`.
- `v4l2_subdev_is_streaming()`, three cases:

  | Sub-device | Reports | Lock asserted |
  |---|---|---|
  | no `enable_streams` | `sd->s_stream_enabled` | none |
  | `enable_streams`, no `V4L2_SUBDEV_FL_STREAMS` | `sd->enabled_pads != 0` | none |
  | `enable_streams` and `V4L2_SUBDEV_FL_STREAMS` | any `enabled` stream config | active state lock |

- Second row: `sd->enabled_pads` is written by
  `v4l2_subdev_set_streams_enabled()` with the active state lock held, but
  the read is not asserted.
- Sub-device with `enable_streams` whose `s_stream` is
  `v4l2_subdev_s_stream_helper()`: `v4l2_subdev_is_streaming()` does not
  read `sd->s_stream_enabled`.
- Third row with no active state: `v4l2_subdev_is_streaming()` dereferences
  NULL; it does not return false.
