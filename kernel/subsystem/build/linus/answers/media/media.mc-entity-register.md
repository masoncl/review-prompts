- `media_entity_pads_init()`: refuses `num_pads >= MEDIA_ENTITY_MAX_PADS` with
  `-E2BIG`, so 512 itself is refused; the macro is private to
  `drivers/media/mc/mc-entity.c`.
- Pad flags: a pad without exactly one of `MEDIA_PAD_FL_SINK` and
  `MEDIA_PAD_FL_SOURCE` gives `-EINVAL`, with no warning.
- `media_entity_pads_init()`: does not touch `entity->links` or any pipeline
  state.
- `entity->links`: initialised only by `media_device_register_entity()`, which
  also zeroes `num_links` and `num_backlinks`.
- Subdevs: `v4l2_subdev_init()` sets `entity.name`, `entity.obj_type` and
  `entity.function = MEDIA_ENT_F_V4L2_SUBDEV_UNKNOWN`; the driver sets
  `function` after that call.
- Video devices: `video_register_media_controller()` does nothing when
  `v4l2_dev->mdev` is NULL or `vfl_dir` is `VFL_DIR_M2M`. Otherwise it writes
  `entity.obj_type` and `entity.function` from `vfl_type`; for every type but
  `VFL_TYPE_RADIO` and `VFL_TYPE_SUBDEV` it also sets `entity.name` and
  registers the entity. The driver sets the pads.
- `graph_obj.mdev`: must be NULL at registration, else `WARN_ON()`; the
  function still goes on and registers.
- **Unsafe usage**: `media_create_pad_link()` with either entity not
  registered, or `media_create_ancillary_link()` with the primary not
  registered; `media_gobj_create()` has `BUG_ON(!mdev)`, and registration
  reinitialises `links`.
  - Safe: register both entities first, as
    `v4l2_m2m_register_media_controller()` does.
- `media_device_unregister_entity()`: calls no `entity_notify` callback.
- `media_device_unregister_entity()` removes, besides the entity: interface
  links in any interface's list whose `entity` is this one; every link in
  `entity->links`, and for a data link its `reverse` in the remote list; the
  pad graph objects; the `internal_idx`.
- Ancillary links: removed only from the entity's own `links`, where it is the
  primary; a link whose `gobj1` is this entity stays in the primary's list.
