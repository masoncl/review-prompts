- `vdev->valid_ioctls`: the only bitmap; there is no separate disable
  bitmap. Before registration a set bit means disabled, after it means
  valid.
- `determine_valid_ioctls()`: called only when `vdev->ioctl_ops` is set.
- Bitmap at registration: nothing clears `vdev->valid_ioctls` first; every
  stale set bit is treated as a disabled ioctl.
- Non-NULL op is not sufficient: buffer ioctls also need
  `V4L2_CAP_STREAMING`, format ioctls on `VFL_TYPE_VIDEO` need a video or
  meta capability in `device_caps`.
- Non-NULL op is not necessary: with `V4L2_CAP_IO_MC` on a video, VBI or
  metadata node the input ioctls (`vfl_dir` not `VFL_DIR_TX`) and the output
  ioctls (`vfl_dir` not `VFL_DIR_RX`) are enabled without ops;
  `VIDIOC_G_PRIORITY` and `VIDIOC_S_PRIORITY` always;
  `VIDIOC_DBG_G_CHIP_INFO`, `VIDIOC_DBG_G_REGISTER` and
  `VIDIOC_DBG_S_REGISTER` always under `CONFIG_VIDEO_ADV_DEBUG`.
- `VIDIOC_QUERYCAP`: enabled only when `vidioc_querycap` is set.
- Event ioctls: `VIDIOC_DQEVENT` and `VIDIOC_SUBSCRIBE_EVENT` follow
  `vidioc_subscribe_event`; no flag is involved.
- There is no V4L2_FL_USE_FH_PRIO in this tree.
- `v4l2_fh_init()` in `drivers/media/v4l2-core/v4l2-fh.c`: sets both
  priority bits in `vdev->valid_ioctls` at every open, so disabling them
  with `v4l2_disable_ioctl()` does not last past the first open.
- Control ioctls (`INFO_FL_CTRL`): `__video_do_ioctl()` lets them through
  with a clear bit when `vfh->ctrl_handler` is set; `v4l2_fh_init()` copies
  `vdev->ctrl_handler` there, so `v4l2_disable_ioctl()` on them has no
  effect for such a handle.
- Disabling `VIDIOC_G_SELECTION`: also leaves `VIDIOC_G_CROP` and
  `VIDIOC_CROPCAP` off; disabling `VIDIOC_S_SELECTION` leaves
  `VIDIOC_S_CROP` off.
- **Unsafe usage**: calling `v4l2_disable_ioctl()` after
  `video_register_device()`; it does `set_bit()`, so it cannot disable
  anything and marks an ioctl valid even when its op is NULL.
  - Safe: before registration, as `vivid_disable_unused_ioctls()` does ahead
    of `vivid_create_devnodes()`.
- **Unsafe usage**: assigning the whole `struct video_device` after
  `v4l2_disable_ioctl()`; the copy overwrites the disabled bits.
  - Safe: copy the template first, then disable, as `vdev_init()` in
    `drivers/media/pci/bt8xx/bttv-driver.c` does.
