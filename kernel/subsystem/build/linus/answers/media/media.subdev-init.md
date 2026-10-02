- `v4l2_subdev_init()`: does not clear `sd->internal_ops`, `sd->ctrl_handler`,
  `sd->state_lock`, `sd->active_state`, `sd->devnode`, `sd->owner` or
  `sd->dev`.
- Those fields are read later, for example `sd->devnode` by
  `__v4l2_device_register_subdev_nodes()` and `sd->state_lock` by
  `__v4l2_subdev_state_alloc()`, so the structure has to start zeroed.
- `sd->entity.function`: `v4l2_subdev_init()` sets it to
  `MEDIA_ENT_F_V4L2_SUBDEV_UNKNOWN`, and `media_device_register_entity()`
  warns if it still has that value.
- `media_entity_pads_init()` does not read `sd->entity.function`; the function
  only has to be set before registration.
- `__v4l2_subdev_init_finalize()` reads these, so all must be final before it
  is called:
  - `sd->ops`, for the stream-op checks
  - `sd->flags`, for `V4L2_SUBDEV_FL_STREAMS`
  - `sd->ctrl_handler`
  - `sd->state_lock`
  - `sd->entity.num_pads`
  - `sd->internal_ops`, for `init_state`
- `v4l2_subdev_cleanup()`: also frees the entries of
  `sd->async_subdev_endpoint_list`, so it is needed after
  `v4l2_async_subdev_endpoint_add()` even without an active state.
- `v4l2_subdev_cleanup()` on a zeroed `sd` that never went through
  `v4l2_subdev_init()`: valid, it returns after the state free.
- `media_entity_cleanup()`: an empty inline in `include/media/media-entity.h`,
  so its place in the removal order changes nothing.
- `v4l2_subdev_cleanup()` and `v4l2_ctrl_handler_free()`: the core imposes no
  order between them; `__v4l2_subdev_state_free()` destroys only
  `state->_lock` and never touches `sd->state_lock`.
