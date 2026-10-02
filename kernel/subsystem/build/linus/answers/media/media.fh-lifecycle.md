- `v4l2_fh_init()`: leaves `fh->prio` at `V4L2_PRIORITY_UNSET`; `v4l2_fh_add()`
  raises it to `V4L2_PRIORITY_DEFAULT` through `v4l2_prio_open()`.
- `v4l2_fh_init()` writes neither `fh->m2m_ctx` nor `fh->navailable`;
  `v4l2_ioctl_get_lock()` and `v4l2_event_dequeue()` read them, so the handle
  must come from zeroed memory, as in `v4l2_fh_open()`.
- `v4l2_fh_init()` overwrites `fh->ctrl_handler` with `vdev->ctrl_handler`; a
  per-open handler is assigned after it.
- `v4l2_fh_open()` allocates with `kzalloc_obj(*fh)`, not a direct `kzalloc()`
  call.
- `v4l2_fh_add()` in `open`: the only ordering it needs is `v4l2_fh_init()`
  first, since it reads `fh->vdev`. It need not be the last step:
  `subdev_open()` in `drivers/media/v4l2-core/v4l2-subdev.c` adds right after
  init and on a later failure unwinds with `v4l2_fh_del()`, `v4l2_fh_exit()`,
  then `kfree()`.
- `v4l2_fh_del()` is what sets `filp->private_data = NULL`; after it
  `file_to_v4l2_fh()` returns `NULL`, so a `release` op fetches its context
  from the file before calling it.
- `v4l2_fh_exit()` sets `fh->vdev = NULL` and returns at once when it is
  already `NULL`; `v4l2_fh_del()` dereferences `fh->vdev`, so it cannot run
  after `v4l2_fh_exit()`.
- `vb2_fop_release()` and `_vb2_fop_release()` end in `v4l2_fh_release()`,
  which calls `kfree()` on the `struct v4l2_fh` pointer itself; they fit only
  a handle that is the start of its own allocation.
