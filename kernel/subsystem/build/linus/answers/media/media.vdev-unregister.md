- `video_unregister_device()`: does not call `cdev_del()`; the cdev, the
  `video_devices[]` slot and the node number stay taken until
  `v4l2_device_release()` runs at the last put.
- `v4l2_event_wake_all()`: called after the flag is cleared; wakes
  `fh->wait` of every `struct v4l2_fh` on `vdev->fh_list`, nothing else.
- `v4l2_ioctl()`: tests `video_is_registered()` with no lock held.
- `__video_do_ioctl()`: tests `video_is_registered()` again after taking the
  lock from `v4l2_ioctl_get_lock()` and returns `-ENODEV`.
- Holding one lock across `video_unregister_device()`: excludes only the
  ioctls that `v4l2_ioctl_get_lock()` maps to that lock, and only for
  drivers whose `unlocked_ioctl` reaches `__video_do_ioctl()`, as
  `video_ioctl2()` does.
- `v4l2_read()`, `v4l2_write()`, `v4l2_poll()`, `v4l2_mmap()`: one unlocked
  test before the driver op, no recheck under any lock.
- `v4l2_poll()` on an unregistered device:
  `EPOLLERR | EPOLLHUP | EPOLLPRI`.
- `v4l2_get_unmapped_area()`: `NULL` under `CONFIG_MMU`; otherwise `-ENOSYS`
  for a missing op is tested before registration, then `-ENODEV`.
- `v4l2_compat_ioctl32()` on an unregistered device: `-ENODEV`.
- `vb2_video_unregister_device()` in
  `drivers/media/common/videobuf2/videobuf2-v4l2.c`: after the unregister it
  calls `vb2_queue_release()` under `queue->lock` or `vdev->lock` and clears
  `queue->owner`; it WARNs when `vdev->queue` is NULL.
