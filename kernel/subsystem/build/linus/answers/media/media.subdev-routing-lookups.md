- `v4l2_subdev_routing_find_opposite_end()`: returns an `int`, `-EINVAL`
  when no route matches; `other_pad` and `other_stream` are left unwritten.
- `v4l2_subdev_routing_find_opposite_end()`: does not test
  `V4L2_SUBDEV_ROUTE_FL_ACTIVE`; it returns the first route in table order
  with a matching end, so an inactive route can hide a later active one.
- `v4l2_subdev_state_get_opposite_stream_format()`: same route match,
  inactive included; the result for an inactive route is `NULL` unless an
  active route has the same opposite pad/stream.
- `v4l2_subdev_state_xlate_streams()`: the only one of the three that uses
  `for_each_active_route()`.
- `v4l2_subdev_state_xlate_streams()`: overwrites `*streams` with the
  subset that had a route; with no match it returns 0 and sets `*streams`
  to 0.
