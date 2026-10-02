- `media_request_lock_for_update()`: succeeds from
  `MEDIA_REQUEST_STATE_IDLE` and from `MEDIA_REQUEST_STATE_UPDATING`; it only
  counts in `updating_count`, so concurrent updaters all succeed.
- `MEDIA_REQUEST_STATE_UPDATING` keeps out `media_request_ioctl_queue()` and
  `media_request_ioctl_reinit()` (both `-EBUSY`), not a second updater; object
  contents need their own lock.
- `media_request_ioctl_reinit()`: accepts IDLE as well as COMPLETE.
- `media_request_lock_for_access()`: called in `.c` files only by
  `v4l2_g_ext_ctrls_request()` in
  `drivers/media/v4l2-core/v4l2-ctrls-request.c`, which returns `-EACCES` for
  a request that is not COMPLETE before it reaches the `-EBUSY` of the lock.
- Objects of a VALIDATING or QUEUED request: read with neither counter held;
  `v4l2_ctrl_request_hdl_find()` WARNs and returns NULL in any other state.
- `req_validate` op: runs in VALIDATING under `mdev->req_queue_mutex`;
  `vb2_request_validate()` walks `req->objects` there without `req->lock`.
- `media_request_object_find()` and `vb2_request_buffer_cnt()`: take
  `req->lock` for the list walk, usable in any state.
- `mdev->req_queue_mutex`: also taken by `media_request_ioctl_reinit()`, by
  `__video_do_ioctl()` for `VIDIOC_STREAMON`, `VIDIOC_STREAMOFF` and
  `VIDIOC_REQBUFS`, and by `v4l2_release()`, each V4L2 case only when
  `v4l2_device_supports_requests()` is true.
- `VIDIOC_QBUF` and `VIDIOC_S_EXT_CTRLS`: do not take `req_queue_mutex`; they
  rely on `media_request_lock_for_update()` alone.
- `req_queue_mutex`, on the paths that take it, is what keeps a vb2 cancel out
  of VALIDATING; `media_request_object_unbind()` WARNs and skips the count in
  that state.
- Lock order: `req_queue_mutex` first, then `q->lock`; see
  `__video_do_ioctl()` and `vb2_req_prepare()`.
