- There is no v4l2_subdev_enable_streams_fallback() here; the `s_stream`
  fallback is inline in `v4l2_subdev_enable_streams()` and
  `v4l2_subdev_disable_streams()`, chosen when the op is absent.
- Returns of `v4l2_subdev_enable_streams()`, in order:

  | Request | Return |
  |---|---|
  | `pad >= sd->entity.num_pads` | `-EINVAL` |
  | pad lacks `MEDIA_PAD_FL_SOURCE` | `-EOPNOTSUPP` |
  | pad index 64 or above | `-EOPNOTSUPP` |
  | `streams_mask` is 0 | 0, nothing done |
  | a requested stream is not on the pad | `-EINVAL` |
  | any requested stream already enabled | `-EALREADY` |

- Kerneldoc in `include/media/v4l2-subdev.h`: says `-EINVAL` for a
  non-source pad and `-EOPNOTSUPP` for several source pads; the code does
  neither.
- Fallback with several source pads: allowed; each pad is a bit in
  `sd->enabled_pads`.
- `v4l2_subdev_collect_streams()`: chooses its branch by
  `V4L2_SUBDEV_FL_STREAMS`, not by which ops exist; without the flag only
  `BIT_ULL(0)` is valid, with or without `enable_streams`.
- Fallback enable: calls `s_stream(1)` only when `sd->s_stream_enabled` is
  false; otherwise it only records the pad.
- Fallback disable: calls `s_stream(0)` only when no other bit remains in
  `sd->enabled_pads`.
- `disable_streams` op returns an error: the error is returned and the
  streams stay marked enabled.
- Fallback disable, driver returns an error: `call_s_stream()` returns 0,
  so the pad is cleared and the caller sees success.
- Entry: both functions read `sd->entity.graph_obj.mdev->dev` before any
  check, so the entity must be registered with a media device.
