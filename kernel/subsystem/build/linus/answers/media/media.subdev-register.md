- Order in `__v4l2_device_register_subdev()`: `v4l2_ctrl_add_handler()`, then
  `media_device_register_entity()`, then `internal_ops->registered()`, then
  `sd->owner = module`, then the list insertion.
- `registered()`: runs with the entity already in the graph (when
  `v4l2_dev->mdev` is set), but with `sd` not yet on `v4l2_dev->subdevs`.
- `sd->name`: an empty name returns `-EINVAL`, in the same test as the NULL
  and already-registered checks.
- Module reference: taken on the `module` argument, not on `sd->owner`; not
  taken when `module` is the owner of the driver of `v4l2_dev->dev`
  (`sd->owner_v4l2_dev`).
- `v4l2_device_register_subdev()` macro in `include/media/v4l2-device.h`:
  passes the caller's `THIS_MODULE`.
- `v4l2_async_match_notify()` and the helpers in
  `drivers/media/v4l2-core/v4l2-i2c.c` and
  `drivers/media/v4l2-core/v4l2-spi.c`: pass `sd->owner`.
- Success overwrites `sd->owner` with `module`;
  `__v4l2_device_register_subdev_nodes()` later uses it as the cdev owner.
- Error path: unless `sd->owner_v4l2_dev` is set, calls `module_put()` on
  `sd->owner`, which is assigned from `module` only after `registered()` has
  succeeded.
- Error path: calls neither `internal_ops->unregistered()` nor
  `internal_ops->release()`.
- `v4l2_ctrl_add_handler()`: also fails registration with the parent
  handler's stored `error` when `sd->ctrl_handler` is set and
  `v4l2_dev->ctrl_handler` is already in error.
