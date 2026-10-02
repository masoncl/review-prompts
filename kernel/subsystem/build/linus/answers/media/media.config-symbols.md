- MEDIA_CONTROLLER_REQUEST_API is not in this tree; the request stubs in
  `include/media/media-request.h` are keyed on `CONFIG_MEDIA_CONTROLLER`.
- `drivers/media/mc/`: `drivers/media/Makefile` enters it only when
  `CONFIG_MEDIA_CONTROLLER` is `y`; inside, `mc.o` is built on
  `CONFIG_MEDIA_SUPPORT`.
- `include/media/media-entity.h`: no configuration guard and no stubs; for
  example `media_entity_pads_init()` and `media_create_pad_link()` are
  defined only in `drivers/media/mc/mc-entity.c`.
- `CONFIG_VIDEO_V4L2_SUBDEV_API`: depends on `VIDEO_DEV && MEDIA_CONTROLLER`
  and has no prompt, so it is on only when something selects it, as
  `VIDEO_CAMERA_SENSOR` in `drivers/media/i2c/Kconfig` does.
- Members that exist only under a symbol; an initialiser or access outside
  the same guard breaks the build:

| Symbol | Guarded members |
|---|---|
| `CONFIG_MEDIA_CONTROLLER` | `entity`, `intf_devnode`, `pipe` in `struct video_device`; `entity` in `struct v4l2_subdev`; `link_validate` in `struct v4l2_subdev_pad_ops` |
| `CONFIG_VIDEO_V4L2_SUBDEV_API` | `state`, `client_caps` in `struct v4l2_subdev_fh` |
| `CONFIG_VIDEO_ADV_DEBUG` | `vidioc_g_register`, `vidioc_s_register`, `vidioc_g_chip_info` in `struct v4l2_ioctl_ops`; `g_register`, `s_register` in `struct v4l2_subdev_core_ops`; the op counters in `struct vb2_queue` and `struct vb2_buffer`, for example `cnt_queue_setup` and `cnt_buf_done` |
| `CONFIG_COMPAT` | `compat_ioctl32` in `struct v4l2_file_operations` and `struct v4l2_subdev_core_ops` |

- `mdev` in `struct v4l2_device` and `active_state` in `struct v4l2_subdev`:
  unconditional.
- Sub-device helpers in `include/media/v4l2-subdev.h`, none with a stub:

| Needs | Helpers |
|---|---|
| nothing | lock helpers, for example `v4l2_subdev_lock_state()` and `v4l2_subdev_lock_and_get_active_state()`; `v4l2_subdev_call()`; `v4l2_subdev_is_streaming()` |
| `CONFIG_MEDIA_CONTROLLER` | `v4l2_subdev_init_finalize()`, `v4l2_subdev_cleanup()`, `v4l2_subdev_link_validate()`, `v4l2_subdev_state_get_format()` and the crop, compose and interval accessors |
| both symbols | for example `v4l2_subdev_get_fmt()`, `v4l2_subdev_set_routing()`, `v4l2_subdev_enable_streams()`, `v4l2_subdev_s_stream_helper()`; everything between the inner guard and its `#endif` |

- There is no v4l2_subdev_get_try_format(), v4l2_subdev_get_try_crop() or
  v4l2_subdev_get_try_compose() here; `v4l2_subdev_state_get_format()` and
  its siblings do that job.
- Without `CONFIG_VIDEO_V4L2_SUBDEV_API`: `subdev_open()`, `subdev_close()`
  and `subdev_ioctl()` in `v4l2-subdev.c` return `-ENODEV`;
  `subdev_do_ioctl()` is not built.
- `v4l2_device_register_subdev_nodes()` and
  `v4l2_device_register_ro_subdev_nodes()` without
  `CONFIG_VIDEO_V4L2_SUBDEV_API`: return 0 and create no node.
- `include/media/media-request.h` stubs without `CONFIG_MEDIA_CONTROLLER`:
  `media_request_lock_for_access()` and `media_request_lock_for_update()`
  return `-EINVAL`; `media_request_object_bind()` returns 0;
  `media_request_object_find()` returns `NULL`.
- No stub without `CONFIG_MEDIA_CONTROLLER`: `v4l2_get_link_freq()` and
  `v4l2_get_active_data_lanes()` in `include/media/v4l2-common.h`;
  `v4l2_create_fwnode_links()` and `v4l2_create_fwnode_links_to_pad()` in
  `include/media/v4l2-mc.h`.
- `v4l2_m2m_register_media_controller()` without `CONFIG_MEDIA_CONTROLLER`:
  stub in `include/media/v4l2-mem2mem.h` returns 0.
- `VIDIOC_DBG_G_REGISTER` and `VIDIOC_DBG_S_REGISTER` with
  `CONFIG_VIDEO_ADV_DEBUG`: both return `-EPERM` without `CAP_SYS_ADMIN`, on
  video nodes (`v4l2-ioctl.c`) and on sub-device nodes (`subdev_do_ioctl()`);
  `VIDIOC_DBG_G_CHIP_INFO` has no capability check.
- `CONFIG_VIDEO_ADV_DEBUG` in
  `drivers/media/common/videobuf2/videobuf2-core.c`: counts each successful
  queue, buffer and memory op, and prints "unbalanced counters" when buffers
  are freed and paired ops differ.
- Without `CONFIG_VIDEO_V4L2_I2C` or `CONFIG_SPI`: stubs in
  `include/media/v4l2-common.h`; the new-subdev functions return `NULL`, the
  init functions do nothing, and `v4l2_i2c_subdev_addr()` returns
  `I2C_CLIENT_END`.
- `CONFIG_VIDEO_FIXED_MINOR_RANGES`: `__video_register_device()` maps the
  node number to the minor one to one inside a fixed range per type; without
  it the minor is the first free one and is independent of the node number.
