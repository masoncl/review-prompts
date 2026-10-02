- `V4L2_FL_SUBDEV_RO_DEVNODE`: set by `__v4l2_device_register_subdev_nodes()`
  from its `read_only` argument, on every node that call creates.
- The read-only choice belongs to the bridge driver, per call; no sub-device
  flag selects it.
- `vdev->device_caps`: not set for a sub-device node;
  `__video_register_device()` exempts `VFL_TYPE_SUBDEV` from that check.
- `vdev->ctrl_handler`: copied from `sd->ctrl_handler` once, at node creation;
  if it is NULL, `__video_register_device()` substitutes
  `v4l2_dev->ctrl_handler`.
- Media interface: created inside `__video_register_device()` by
  `video_register_media_controller()`; `__v4l2_device_register_subdev_nodes()`
  only adds the link.
- Error path of `__v4l2_device_register_subdev_nodes()`: walks
  `v4l2_dev->subdevs` from the head and stops at the first sub-device whose
  `sd->devnode` is NULL, so nodes behind it stay registered.
- That error path also unregisters nodes that an earlier successful call
  created.
- Read-only tests: search `ro_subdev` in `subdev_do_ioctl()` in
  `drivers/media/v4l2-core/v4l2-subdev.c`; there are seven, all `-EPERM`, and
  none in `subdev_do_ioctl_lock()`.

| ioctl | Refused on a read-only node |
|---|---|
| `VIDIOC_SUBDEV_S_FMT`, `VIDIOC_SUBDEV_S_CROP`, `VIDIOC_SUBDEV_S_SELECTION`, `VIDIOC_SUBDEV_S_FRAME_INTERVAL`, `VIDIOC_SUBDEV_S_ROUTING` | when `which` is not `V4L2_SUBDEV_FORMAT_TRY` |
| `VIDIOC_SUBDEV_S_STD`, `VIDIOC_SUBDEV_S_DV_TIMINGS` | always |
| `VIDIOC_S_EDID`, `VIDIOC_SUBDEV_S_CLIENT_CAP`, `VIDIOC_S_CTRL`, `VIDIOC_S_EXT_CTRLS`, `VIDIOC_DBG_S_REGISTER`, anything passed to the `ioctl` core op | never |

- `VIDIOC_SUBDEV_S_FRAME_INTERVAL` from a client without
  `V4L2_SUBDEV_CLIENT_CAP_INTERVAL_USES_WHICH`: `subdev_ioctl_get_state()`
  forces `which` to `V4L2_SUBDEV_FORMAT_ACTIVE` first, so a read-only node
  always refuses it.
