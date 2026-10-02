- `__v4l2_async_register_subdev()` refuses one thing: an `sd->fwnode` that is
  a graph endpoint, with `-EINVAL`.
- Missing fwnode: not refused; `sd->fwnode` stays NULL when `sd->dev` is NULL
  or `dev_fwnode(sd->dev)` is NULL.
- Already registered sub-device: not refused; the function re-initialises
  `sd->asc_list` and adds `sd->async_list` to `subdev_list` again.
- NULL `sd->dev`: refused only by `__v4l2_async_register_subdev_sensor()`,
  with `WARN_ON()` and `-ENODEV`.
- Duplicate matches: checked for connections in
  `v4l2_async_nf_match_valid()`, never for sub-devices.
- Refusals at bind time: `__v4l2_device_register_subdev()` returns `-EINVAL`
  for an empty `sd->name` or a set `sd->v4l2_dev`, and `-ENODEV` when
  `try_module_get()` fails.
- Bind-time error: returned by whichever call ran the match, which can be
  the bridge's `v4l2_async_nf_register()` rather than the sub-device's
  register call.
- `match_fwnode_one()`: tests only the connection's fwnode with
  `fwnode_graph_is_endpoint()`, then compares its port parent with the
  sub-device fwnode.
- Connection holding a device node: matches by pointer equality only, with
  `sd->fwnode` or `sd->fwnode->secondary`.
- `v4l2_async_subdev_endpoint_add()`: stores the endpoint pointer and takes
  no reference; the driver keeps the endpoint alive for as long as the
  sub-device is registered, as `adv748x_remove()` does by calling
  `adv748x_dt_cleanup()` after `adv748x_csi2_cleanup()`.
- `subdev_list`: the sub-device is added whether or not it was bound, so a
  notifier registered later can bind it again.
- **Unsafe usage**: registering with `sd->fwnode` NULL and no fwnode on
  `sd->dev`, when a notifier tries a waiting `V4L2_ASYNC_MATCH_TYPE_FWNODE`
  connection against the sub-device, at registration or later.
  - Unsafe: `match_fwnode()` reads `sd->fwnode->secondary` with no NULL test
    once `match_fwnode_one()` has failed.
  - Safe: `sd->fwnode` left NULL and `sd->dev` set to a device that has a
    fwnode, as `v4l2_i2c_subdev_init()` sets it;
    `__v4l2_async_register_subdev()` fills `sd->fwnode` from `dev_fwnode()`.
  - Safe: a non-empty `sd->async_subdev_endpoint_list`, as
    `adv748x_csi2_init()` sets up; `match_fwnode()` returns before it
    dereferences `sd->fwnode`.
- **Unsafe usage**: registering a sub-device's own notifier after
  `v4l2_async_register_subdev()`.
  - Unsafe: when the sub-device was bound inside its register call, the
    notifier gets no `parent`; `v4l2_async_nf_try_subdev_notifier()` runs
    only when the sub-device is bound, so the notifier binds nothing until
    the sub-device is bound again.
  - Safe: `v4l2_async_nf_register()` first, then the sub-device, as
    `__v4l2_async_register_subdev_sensor()` does;
    `v4l2_async_nf_try_subdev_notifier()` finds only a notifier that is
    already on `notifier_list`.
