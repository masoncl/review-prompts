- `struct media_entity`: not always embedded in a `struct video_device` or a
  `struct v4l2_subdev`. `obj_type` `MEDIA_ENTITY_TYPE_BASE` marks the rest,
  for example the entities that `dvb_create_media_entity()` in
  `drivers/media/dvb-core/dvbdev.c` allocates.
- mem2mem node in the graph: `video_register_media_controller()` skips
  `VFL_DIR_M2M`. `v4l2_m2m_register_media_controller()` registers three
  entities instead: `&vdev->entity` as source, plus `proc` and `sink`
  embedded in `struct v4l2_m2m_dev`.
- mem2mem entities: all three get `MEDIA_ENTITY_TYPE_BASE`, so
  `is_media_entity_v4l2_video_device()` is false even for the one embedded
  in the `struct video_device`.
- `struct media_link`: three kinds, told apart by
  `link->flags & MEDIA_LNK_FL_LINK_TYPE`:

  | Kind | Ends | List it is on | Created by |
  |---|---|---|---|
  | data | `source` pad, `sink` pad | `links` of each entity | `media_create_pad_link()` |
  | interface | `intf`, `entity` | `links` of the interface | `media_create_intf_link()` |
  | ancillary | `gobj0`, `gobj1`, both entities | `links` of the primary entity | `media_create_ancillary_link()` |

- `struct media_pipeline`: a set of pads, not of entities.
  `media_pipeline_start()` takes a `struct media_pad` and sets `pad->pipe`
  on every pad it reaches.
- Pads of one entity: can be in different pipelines when the entity's
  `has_pad_interdep` op says they are independent.
  `media_entity_pipeline()` returns the pipe of the first pad that has one.
- `struct media_pipeline` storage, three choices: a driver's own object; the
  `pipe` member of `struct video_device`; or one that
  `media_pipeline_alloc_start()` allocates and `__media_pipeline_stop()`
  frees when `start_count` reaches zero.
- `media_pipeline_start()`: collects pads and calls `link_validate` on
  enabled links. It starts no hardware; the driver calls
  `v4l2_subdev_enable_streams()` or the `s_stream` op itself.
- `struct media_devnode`: this, not `struct media_device`, is `/dev/mediaN`.
  `__media_device_register()` allocates it; it has its own `struct device`
  and is freed in `media_devnode_release()` on the last put.
- `struct media_device`: has no reference count of its own.
- `v4l2_fh_add()` and `v4l2_fh_del()`: both take the `struct file` as well
  as the `struct v4l2_fh`; that is how they set and clear
  `file->private_data`.
- `struct v4l2_subdev_fh`: embeds a `struct v4l2_fh`, so subdev nodes use the
  same per-open object as video nodes.
- Subdev node: a separate `struct video_device` that
  `__v4l2_device_register_subdev_nodes()` allocates and stores in
  `sd->devnode`. The way back is `vdev_to_v4l2_subdev()`, which reads
  driver data, not `container_of()`.
- Subdev node in the graph: the `entity` member of that `struct video_device`
  is not registered; the interface link goes to `sd->entity`.
- `struct v4l2_device` reference count: `v4l2_device_register()` starts it
  at one for the driver, and each registered `struct video_device` takes one
  more.
- `v4l2_device_unregister()`: does not drop the driver's reference;
  `v4l2_device_put()` does. The `release` callback needs both the last node
  gone and that put.
- Active `struct v4l2_subdev_state`: exists only after
  `__v4l2_subdev_init_finalize()`, which the `v4l2_subdev_init_finalize()`
  macro calls. Otherwise `sd->active_state` is NULL and pad ops receive a
  NULL state for `V4L2_SUBDEV_FORMAT_ACTIVE`; see
  `subdev_ioctl_get_state()`.
- `struct v4l2_ctrl_handler` lock: the member is `lock`, which defaults to
  `_lock`. `ctrl_lock` is not a member of the handler.
- `struct vb2_v4l2_buffer`: embeds `struct vb2_buffer` as `vb2_buf`, and a
  driver's buffer struct embeds `struct vb2_v4l2_buffer`.
- Buffer allocation: vb2 allocates each buffer itself, `q->buf_struct_size`
  bytes in `__vb2_queue_alloc()`, and uses the start of it as the
  `struct vb2_buffer`.
- `struct v4l2_async_connection`: one connection, not one subdev. A subdev
  can hold several on `sd->asc_list`; `v4l2_async_connection_unique()`
  returns NULL unless there is exactly one.
- Async match: by fwnode or by I2C adapter and address, see
  `enum v4l2_async_match_type`.
- `struct v4l2_m2m_dev`: opaque to drivers, defined in
  `drivers/media/v4l2-core/v4l2-mem2mem.c`. It has a `kref`:
  `v4l2_m2m_put()` frees on the last reference, `v4l2_m2m_release()` frees
  at once.
- DVB, RC and CEC: of the three, only DVB adds objects to the media graph, in
  `drivers/media/dvb-core/dvbdev.c` under `CONFIG_MEDIA_CONTROLLER_DVB`.
  Nothing under `drivers/media/rc/` or `drivers/media/cec/` references graph
  objects.
