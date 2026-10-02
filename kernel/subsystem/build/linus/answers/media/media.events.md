- `fh->subscribed`: writers hold both `fh->subscribe_lock` (mutex) and
  `vdev->fh_lock`; `__v4l2_event_unsubscribe()` asserts both. The queue path
  takes only `vdev->fh_lock`.
- `v4l2_event_queue()`: tests no flag; it returns when `vdev` is `NULL` and
  otherwise walks `vdev->fh_list`.
- `vdev->fh_lock` and `vdev->fh_list` are initialised in
  `__video_register_device()`, not when the `struct video_device` is
  allocated.
- `replace` and `merge` of `struct v4l2_subscribed_event_ops` run inside
  `__v4l2_event_queue_fh()` under `vdev->fh_lock` with interrupts off, in the
  context of whoever queued the event; `add` and `del` run under
  `fh->subscribe_lock`, with `vdev->fh_lock` released.
- `fh->sequence`: incremented only after a subscription matched the type and
  id; an event with no subscription on that handle leaves it unchanged.
- Full queue with `sev->elems == 1`: `replace(old, new)` is called if set and
  the core then skips copying `ev->u`, so `replace` must leave the final
  payload in its first argument; `merge` is not called in this case.
- Full queue with `sev->elems` above 1: `merge(oldest, second_oldest)` is
  called if set; `replace` is not called.
- Full queue with no matching op: the oldest event of that subscription is
  dropped and the new one stored.
- **Unsafe usage**: calling `v4l2_event_dequeue()` with `nonblocking` 0 while
  `fh->vdev->lock` is set and the caller does not hold it; the function calls
  `mutex_unlock()` on it without testing that it is held.
  - Safe: from `v4l_dqevent()`; `__video_do_ioctl()` holds the mutex chosen by
    `v4l2_ioctl_get_lock()`, which is `vdev->lock` for `VIDIOC_DQEVENT`.
  - Safe: from `subdev_do_ioctl()`; `__v4l2_device_register_subdev_nodes()`
    leaves `vdev->lock` `NULL`, so `v4l2_event_dequeue()` skips the unlock,
    and `subdev_do_ioctl_lock()` takes `vdev->lock` whenever it is set.
  - Safe: with `nonblocking` nonzero, as `v4l_dqevent()` passes for an
    `O_NONBLOCK` file; `v4l2_event_dequeue()` returns before it touches
    `vdev->lock`.
- `v4l2_event_dequeue()` retakes `fh->vdev->lock` with `mutex_lock()` also
  when the wait was interrupted, so it returns `-ERESTARTSYS` with the lock
  held.
