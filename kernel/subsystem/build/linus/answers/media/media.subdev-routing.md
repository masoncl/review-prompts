- Core checks before `set_routing`, in order:

  | Check | Result |
  |---|---|
  | `len_routes > 256`, in `check_array_args()` | `-E2BIG` |
  | `v4l2_subdev_enable_streams_api` false | `-ENOIOCTLCMD` |
  | no `V4L2_SUBDEV_FL_STREAMS` | `-ENOIOCTLCMD` |
  | no `V4L2_SUBDEV_CLIENT_CAP_STREAMS` on the file handle | `-EINVAL` |
  | `which` not `V4L2_SUBDEV_FORMAT_TRY` on a read-only node | `-EPERM` |
  | `num_routes > len_routes` | `-EINVAL` |
  | a stream id above `V4L2_SUBDEV_MAX_STREAM_ID` (63) | `-EINVAL` |
  | pad out of range or wrong direction | `-EINVAL` |
  | active routes above `V4L2_FRAME_DESC_ENTRY_MAX` | `-E2BIG` |

- `which`: not validated for routing; `check_which()` is not called, and
  any value other than `V4L2_SUBDEV_FORMAT_TRY` selects the active state in
  `subdev_ioctl_get_state()`.
- Streaming: the core makes no test; `-EBUSY` comes only from the driver's
  `set_routing`.
- `v4l2_subdev_routing_validate()`: called only by drivers, never by the
  core.
- `v4l2_subdev_routing_validate()` on a violation: returns `-ENXIO`, not
  `-EINVAL`; `-ENOMEM` if its scratch array cannot be allocated.
- `v4l2_subdev_routing_validate()`: walks every route, inactive ones
  included, so an inactive route can violate a restriction.
- `v4l2_subdev_routing_validate()` with `disallow` 0: checks pad index and
  direction only; duplicate ends pass.
- `v4l2_subdev_set_routing()`: takes no format argument and does not
  validate the routes; only `v4l2_subdev_set_routing_with_fmt()` takes a
  format.
- `v4l2_subdev_set_routing_with_fmt()`: writes `fmt` only; crop, compose
  and interval of every stream config stay zero.
- Old stream configs: the whole array is replaced by a new one, zeroed
  except for `pad` and `stream`, so the `enabled` flag of every stream is
  cleared along with the formats.
- **Unsafe usage**: on a state of a `V4L2_SUBDEV_FL_STREAMS` sub-device,
  using a pointer from `v4l2_subdev_state_get_format()` (or the crop,
  compose, interval accessors) taken before `v4l2_subdev_set_routing()`;
  `v4l2_subdev_init_stream_configs()` frees the old array.
  - Safe: fetch the pointer after the call, as `_ub913_set_routing()` in
    `drivers/media/i2c/ds90ub913.c` does.
- **Potentially unsafe usage**: `v4l2_subdev_set_routing()` on the active
  state.
  - Unsafe: while streams are enabled; `enabled` is lost, so
    `v4l2_subdev_is_streaming()` reports false and
    `v4l2_subdev_disable_streams()` returns `-EALREADY` or `-EINVAL`
    without calling the op.
  - Safe: the driver returns `-EBUSY` first for
    `V4L2_SUBDEV_FORMAT_ACTIVE` while streaming, as
    `mxc_isi_crossbar_set_routing()` does with
    `media_entity_is_streaming()`.
