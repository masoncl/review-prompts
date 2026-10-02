- Sink entity not a sub-device: `WARN_ON_ONCE()` and `-EINVAL`.
- Source is a video device: the result is that of the source entity's
  `link_validate`.

  | Source video device | Result |
  |---|---|
  | `ops` or `link_validate` missing | `pr_warn_once()`, returns 0 |
  | `link_validate` is `v4l2_subdev_link_validate()` | `WARN_ON()`, `-EINVAL` |
  | otherwise | return of its `link_validate` |

- Source neither video device nor sub-device: `WARN_ON()` and `-EINVAL`.
- Locking: both active states come from
  `v4l2_subdev_get_unlocked_active_state()`; `v4l2_subdev_lock_states()` takes
  them only when both are non-NULL, sink first.
- Either active state NULL: nothing is held across the validation;
  `v4l2_subdev_link_validate_get_format()` and
  `__v4l2_link_validate_get_streams()` lock and unlock around each call with
  `v4l2_subdev_lock_and_get_active_state()`.
- Caller precondition: neither active-state lock may be held when the pipeline
  starts; `v4l2_subdev_get_unlocked_active_state()` has
  `lockdep_assert_not_held()`, and `v4l2_subdev_lock_states()` then does
  `mutex_lock()`.
- Stream masks: for a sub-device with `V4L2_SUBDEV_FL_STREAMS`, built per link
  end by `__v4l2_link_validate_get_streams()` from `for_each_active_route()`,
  under `CONFIG_VIDEO_V4L2_SUBDEV_API`; without the flag the mask is
  `BIT_ULL(0)`. `v4l2_subdev_has_pad_interdep()` is not called.
- Sink stream with no source stream of the same number: `dev_err()` and
  `-EINVAL`, before any format is read.
- Unreadable format: any negative return from `get_fmt` on either end skips
  that stream with `continue`, without an error.
- What counts as unreadable: also `-ENOIOCTLCMD` when the sub-device has no
  `get_fmt` op, and `-EINVAL` from `check_state()` when a
  `V4L2_SUBDEV_FL_STREAMS` sub-device has no format for that pad and stream.
- A skipped stream reaches neither the `link_validate` pad op nor
  `v4l2_subdev_link_validate_default()`.
- `v4l2_subdev_link_validate_default()`: compares `width`, `height`, `code`
  and `field` only; `field` also passes when the sink has `V4L2_FIELD_NONE`.
- `v4l2_subdev_link_validate_default()` does not compare `colorspace`,
  `ycbcr_enc`, `quantization`, `xfer_func` or stream numbers.
