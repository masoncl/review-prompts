- `v4l2_subdev_release()`: static in `drivers/media/v4l2-core/v4l2-device.c`,
  with two callers, `v4l2_device_unregister_subdev()` when there is no node
  and `v4l2_device_release_subdev_node()` when there is.
- With a node, `release` is driven by the `struct device` inside
  `struct video_device`, through `v4l2_device_release()` in
  `drivers/media/v4l2-core/v4l2-dev.c`; the media entity plays no part.
- `v4l2_device_unregister_subdev()` on a sub-device with `sd->v4l2_dev` NULL:
  returns at once, so neither `unregistered` nor `release` runs.
- A sub-device that was never registered, or whose registration failed, never
  gets `release`; memory freed only from `release` is then not freed.
- `v4l2_subdev_release()`: reads `sd->owner` and `sd->owner_v4l2_dev` before
  it calls `internal_ops->release()`.
- `v4l2_device_unregister()`: reads `sd->flags` after
  `v4l2_device_unregister_subdev()` has returned, which for a sub-device
  without a node is after `release`.
- `sd->active_state`: not read by `subdev_close()` or `v4l2_subdev_release()`.
- After unregistration `subdev_do_ioctl_lock()` returns `-ENODEV` before
  `subdev_ioctl_get_state()` runs, so the core does not need
  `v4l2_subdev_cleanup()` to wait for `release`.
- In-flight ioctls: `video_unregister_device()` does not wait for an ioctl
  that has already passed the `video_is_registered()` test, and sub-device
  nodes have no `vdev->lock`.
- **Potentially unsafe usage**: freeing the memory that holds the
  `struct v4l2_subdev` when `v4l2_device_unregister_subdev()` returns, by
  `kfree()` in `remove()` or by devres.
  - Unsafe: when a node was registered (`sd->devnode` set) and a file handle
    is still open; `subdev_close()` reads `sd->internal_ops`, and
    `v4l2_subdev_release()` then reads and writes `sd`.
  - Safe: when no node was ever registered for `sd`, because
    `v4l2_device_unregister_subdev()` calls `v4l2_subdev_release()` before it
    returns; `tuner_remove()` in `drivers/media/v4l2-core/tuner-core.c` frees
    right after it.
