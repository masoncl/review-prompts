- Flag names: the table flags are `INFO_FL_PRIO`, `INFO_FL_CTRL`,
  `INFO_FL_QUEUE`, `INFO_FL_ALWAYS_COPY` and `INFO_FL_CLEAR()`; there is no
  INFO_FL_STD or INFO_FL_FUNC.
- `INFO_FL_CLEAR()`: zeroes everything after the named field, input fields
  included, not only `reserved`.
- Without `INFO_FL_CLEAR()`: reserved fields reach the handler as user space
  wrote them; `video_get_user()` rejects nothing. The handler or driver
  zeroes them, for example `v4l_reqbufs()` with `memset_after()`.
- `'V'` numbers: shared by `include/uapi/linux/videodev2.h` and
  `include/uapi/linux/v4l2-subdev.h`, since both node types use
  `video_usercopy()`.
  - `video_get_user()` and `check_array_args()` match on the full command
    value, so a `v4l2_ioctls` flag also applies on a sub-device node when
    the values are equal, as for `VIDIOC_SUBDEV_G_EDID` and `VIDIOC_G_EDID`.
  - A new command must not equal an existing one of the other header unless
    the argument handling is meant to be shared.
- New video ioctl, easy to miss:
  - number below `BASE_VIDIOC_PRIVATE`; `valid_ioctls` has that many bits;
  - `func` in `IOCTL_INFO()` is called with no NULL test;
  - `determine_valid_ioctls()` in `drivers/media/v4l2-core/v4l2-dev.c` must
    set the bit, or `__video_do_ioctl()` returns `-ENOTTY`.
- Command not in the table, also a known number with another size: goes to
  `vidioc_default` with no `valid_ioctls` test; the priority result is
  passed as an argument, not enforced.
- New sub-device ioctl, besides the `case` in `subdev_do_ioctl()`:
  - add it to `subdev_ioctl_get_state()` if it has `which`, or `state` is
    NULL;
  - zero `reserved`, and `stream` without `V4L2_SUBDEV_CLIENT_CAP_STREAMS`,
    by hand;
  - return `-EPERM` for a setter on `V4L2_FL_SUBDEV_RO_DEVNODE`, as the
    `VIDIOC_SUBDEV_S_FMT` case does when `which` is not
    `V4L2_SUBDEV_FORMAT_TRY`;
  - an array argument needs `check_array_args()`, and copy-back on error
    needs its own test in `video_usercopy()`.
- Media ioctls: the file is `drivers/media/mc/mc-device.c`; add with
  `MEDIA_IOC()` to `ioctl_info`.
  - `media_device_ioctl()` matches the full command; a resized struct gets
    `-ENOIOCTLCMD`.
  - It copies in all `_IOC_SIZE` bytes of a command with `_IOC_WRITE` and
    copies out only when the handler returned 0.
  - Reserved fields are zeroed by each handler, for example
    `media_device_enum_links()`.
  - Request ioctls are in `media_request_ioctl()` in
    `drivers/media/mc/mc-request.c`.
