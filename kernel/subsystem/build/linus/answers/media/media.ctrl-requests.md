- `struct v4l2_ctrl_ref`: the request value is `p_req`, `p_req_valid` says the
  request holds a value, `req_done` is scratch for
  `v4l2_ctrl_request_setup()`; there is no field named req.
- No control flag makes a control mandatory in a request; a driver checks
  that in its `req_validate` op.
- `v4l2_ctrl_request_hdl_ctrl_find()`: returns NULL for a control the request
  did not set (`p_req_valid` false), not only for an unknown id.
- `v4l2_ctrl_request_setup()`: applies whole clusters; if any member has
  `p_req_valid` the other members are written with their current values.
- `v4l2_ctrl_request_setup()`: skips controls with
  `V4L2_CTRL_FLAG_READ_ONLY`.
- `v4l2_ctrl_request_setup()` return: 0 when the request has no control
  object, `-EBUSY` when the request is not QUEUED (with WARN) or the object is
  already completed.
- `v4l2_ctrl_request_complete()`: for `V4L2_CTRL_FLAG_VOLATILE` controls it
  calls `g_volatile_ctrl` and overwrites `p_req` even if the request set the
  control.
- `v4l2_ctrl_request_complete()` with `req` NULL: returns without doing
  anything.
- **Potentially unsafe usage**: calling `v4l2_ctrl_request_complete()` after
  the last buffer of the request was returned.
  - Unsafe: when the request is not marked for manual completion and holds no
    control object; the request is already COMPLETE, so
    `media_request_object_bind()` WARNs, returns `-EBUSY`, and no values are
    stored.
  - Safe: when the request is marked for manual completion and so still
    QUEUED, as `device_run()` in
    `drivers/media/test-drivers/vicodec/vicodec-core.c`.
  - Safe: complete the controls first, then return the buffer, as
    `vim2m_stop_streaming()` in `drivers/media/test-drivers/vim2m.c`.
