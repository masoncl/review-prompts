- `struct v4l2_fh` is mandatory: after a successful `vdev->fops->open()`,
  `v4l2_open()` in `drivers/media/v4l2-core/v4l2-dev.c` tests
  `V4L2_FL_USES_V4L2_FH` in `vdev->flags`; if clear it hits `WARN_ON()`, calls
  `vdev->fops->release()`, drops the device reference and returns `-ENODEV`.
- `V4L2_FL_USES_V4L2_FH` is defined in `include/media/v4l2-dev.h` and set by
  `v4l2_fh_init()`, not by `v4l2_fh_add()`.
- The test in `v4l2_open()` is per device, not per file: the bit stays set
  once any open has called `v4l2_fh_init()` on that `struct video_device`, and
  `filp->private_data` is not examined.
- **Unsafe usage**: an `open` op that returns 0 without having called
  `v4l2_fh_add()` on the file; `__video_do_ioctl()` reads `vfh->prio` and
  `vfh->ctrl_handler` from `file_to_v4l2_fh()` with no `NULL` test, and
  `vb2_poll()` reads `fh->wait` the same way.
  - Safe: `v4l2_fh_init()` then `v4l2_fh_add()` before returning 0, as
    `v4l2_fh_open()` does; `v4l2_fh_add()` sets `filp->private_data`.
- `V4L2_FL_USES_V4L2_FH` is tested nowhere but `v4l2_open()`.
