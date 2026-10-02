- VB2_BUF_STATE_REQUEUEING is not in this tree; `enum vb2_buffer_state` has
  seven values and `vb2_buffer_done()` accepts three of them.
- `queued_list`: the buffer stays on it for every target state;
  `vb2_core_dqbuf()` removes it.
- Request buffer, target not `VB2_BUF_STATE_QUEUED`: calls
  `media_request_object_unbind()` and `media_request_object_put()` under
  `q->done_lock`; it does not call `media_request_object_complete()`.
- After a call with target `VB2_BUF_STATE_DONE` or `VB2_BUF_STATE_ERROR`,
  `vb->req_obj.req` is NULL.
- **Potentially unsafe usage**: `v4l2_ctrl_request_complete()` after
  `vb2_buffer_done()` returned the request's buffer with
  `VB2_BUF_STATE_DONE` or `VB2_BUF_STATE_ERROR`.
  - Unsafe: passing `vb->req_obj.req` read after the buffer was returned; it
    is NULL and `v4l2_ctrl_request_complete()` returns without completing the
    control object.
  - Safe: complete the controls first, as `vivid_stop_generating_vid_cap()`
    in `drivers/media/test-drivers/vivid/vivid-kthread-cap.c` does.
  - Safe: the request pointer was copied before the buffer was returned and
    the request is marked with `media_request_mark_manual_completion()`, as
    `device_run()` in `drivers/media/test-drivers/vicodec/vicodec-core.c`
    does; the request stays QUEUED until `media_request_manual_complete()`.
