- `vdev->release`: runs on no failure path of `__video_register_device()`.
- `device_register()` failure: the core does not call `put_device()`; it
  goes straight to `cleanup`.
- `vdev->dev.release`: assigned `v4l2_device_release()` only after
  `device_register()` succeeded.
- Caller after any failure: frees the vdev itself exactly once, as
  `__v4l2_device_register_subdev_nodes()` does with `kfree(vdev)`.
- `fops` check: `-EINVAL` with `WARN_ON` when `vdev->fops`, `fops->open` or
  `fops->release` is NULL, before anything is reserved.
- `V4L2_FL_REGISTERED`: never set on a failure path.
- `video_unregister_device()` after a failed registration: returns early
  when `video_is_registered()` is false, frees nothing; the vdev memory must
  still exist.
- `v4l2_device_get()`: called only after `device_register()` succeeded; a
  failed registration holds no `struct v4l2_device` reference.
- `video_register_media_controller()` failure: ignored;
  `__video_register_device()` still sets `V4L2_FL_REGISTERED` and returns 0.
