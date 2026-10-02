- NULL state: `__v4l2_subdev_state_get_format()`,
  `__v4l2_subdev_state_get_crop()` and `__v4l2_subdev_state_get_compose()`
  return NULL after `WARN_ON_ONCE()`; `__v4l2_subdev_state_get_interval()`
  uses `WARN_ON()`, so it warns on every call.
- Missing pad or stream: returns NULL silently on both paths; no warning.
- `lockdep_assert_held(state->lock)`: format, crop and compose assert only
  on the streams path, after the `pads` branch has returned;
  `__v4l2_subdev_state_get_interval()` asserts before the `pads` branch, so
  for every non-NULL state.
- Streams state: entries exist only for the two ends of each route with
  `V4L2_SUBDEV_ROUTE_FL_ACTIVE`; `v4l2_subdev_init_stream_configs()` builds
  them from `for_each_active_route()`. A pad and stream that only inactive
  routes use returns NULL.
- New streams state: holds no entries until `init_state` calls
  `v4l2_subdev_set_routing()`; until then every accessor returns NULL.
- Ops with no wrapper entry, for example `set_routing`: `v4l2_subdev_call()`
  passes the state as given, NULL included.
