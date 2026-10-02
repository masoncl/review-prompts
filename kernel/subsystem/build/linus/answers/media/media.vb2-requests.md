- `min_queued_buffers` must be 0 when `supports_requests` is set;
  `vb2_core_queue_init()` WARNs and returns `-EINVAL` otherwise.
- Missing `buf_request_complete`: detected only at the first request QBUF, in
  `vb2_queue_or_prepare_buf()` in
  `drivers/media/common/videobuf2/videobuf2-v4l2.c`, as WARN and `-EINVAL`.
- Missing `buf_out_validate`: same check, but only for queue types
  `V4L2_BUF_TYPE_VIDEO_OUTPUT` and `V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE`.
- Request QBUF runs `buf_out_validate` only (output queue, buffer not yet
  prepared); `buf_prepare` runs later, from `vb2_req_prepare()` during
  `MEDIA_REQUEST_IOC_QUEUE`.
- `vb2_request_validate()`: calls the `prepare` op of every object that has
  one; the control object's `req_ops` has none, so it validates no controls.
- A buffer prepared with `VIDIOC_PREPARE_BUF` can be queued in a request; it
  is in `VB2_BUF_STATE_DEQUEUED` and `vb2_core_qbuf()` skips
  `buf_out_validate` for it.
- `vb2_prepare_buf()`: refuses `V4L2_BUF_FLAG_REQUEST_FD` with `-EINVAL`.
- Request QBUF of a buffer not in `VB2_BUF_STATE_DEQUEUED`: `-EINVAL`;
  `-EBUSY` is what a direct QBUF gets while `uses_requests` is set and
  `requires_requests` is clear.
- `v4l2_m2m_qbuf()`: refuses a request on the capture queue with `-EPERM`.
- `uses_requests` and `uses_qbuf`: cleared in `__vb2_queue_cancel()`, reached
  from `vb2_core_streamoff()`, `vb2_core_queue_release()` and the freeing
  path of `vb2_core_reqbufs()`.
- `buf_request_complete`: called from `__vb2_queue_cancel()` only for a
  buffer whose request is in `MEDIA_REQUEST_STATE_QUEUED`; a buffer in an
  IDLE request is unbound without the callback.
