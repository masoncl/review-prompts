- `struct media_devnode`: allocated in `__media_device_register()`;
  `mdev->devnode` is a pointer, not an embedded structure.
- `media_device_unregister()`: after a NULL test of `mdev` it locks
  `graph_mutex` before any other test, so `media_device_init()` must have run;
  with that done it returns early when `mdev->devnode` is NULL or not
  registered.
- `media_device_unregister()`: removes the `model` attribute and calls
  `media_devnode_unregister()` after it has dropped `graph_mutex`.
- `media_devnode_release()`: calls `devnode->release` and frees the devnode; it
  does not release the minor. `media_devnode_unregister()` clears the bit in
  `media_devnode_nums`, so the minor can be reused while old files are open.
- `media_devnode_unregister()`: sets `devnode->media_dev` to NULL.
- Open file on the media node: holds a reference on the devnode only, not on
  the `struct media_device`.
- After unregistration: ioctl returns `-EIO`, open returns `-ENXIO`, poll
  returns `EPOLLERR | EPOLLHUP`; see `drivers/media/mc/mc-devnode.c`.
- Read and write on the media node: `-EINVAL` before and after unregistration,
  because `media_device_fops` has neither op.
- Request fd: holds no reference on the media device or devnode, and
  `media_request_release()` and the request ioctls in
  `drivers/media/mc/mc-request.c` use `req->mdev` (`ops`, `req_queue_mutex`,
  `num_requests`) for as long as the fd is open.
- Entities after `media_device_unregister()`: every entity and pad has
  `graph_obj.mdev == NULL`. `media_device_unregister_entity()` then returns at
  once; `media_pipeline_start()` and `v4l2_pipeline_pm_get()` dereference it
  with no NULL test.
- Interfaces: `media_device_unregister()` unlinks them and does not free them;
  `media_devnode_remove()` afterwards is safe and frees the interface.
- `media_device_cleanup()`: destroys the ida, `pm_count_walk`, `graph_mutex`
  and `req_queue_mutex`; it touches no request.
- Cleanup from a release callback: see `vimc_v4l2_dev_release()` in
  `drivers/media/test-drivers/vimc/vimc-core.c`.
- Refcounted media device: `media_device_usb_allocate()` and
  `media_device_delete()` in `drivers/media/mc/mc-dev-allocator.c`; the last
  put calls `media_device_unregister()`, `media_device_cleanup()`, `kfree()`.
