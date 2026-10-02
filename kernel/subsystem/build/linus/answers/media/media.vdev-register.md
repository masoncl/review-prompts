- `vdev->fops`, `fops->open`, `fops->release`: mandatory;
  `__video_register_device()` WARNs and returns `-EINVAL` without them.
- `vdev->fops->owner`: read by `video_register_device()` and
  `video_register_device_no_warn()` before any check, and used as the cdev
  owner; a NULL `fops` is dereferenced there.
- Missing `vdev->release`: `__video_register_device()` WARNs and returns
  `-EINVAL`.
- Zeroed struct: required; the core uses `vdev->flags` and
  `vdev->valid_ioctls` without initialising them.
- First successful open: after `set_bit(V4L2_FL_REGISTERED)`, the last step
  of `__video_register_device()`, not after `cdev_add()` or
  `device_register()`.
- `videodev_lock`: held from before `device_register()` until the flag is
  set; `v4l2_open()` takes it, so an earlier open waits or gets `-ENODEV`.
