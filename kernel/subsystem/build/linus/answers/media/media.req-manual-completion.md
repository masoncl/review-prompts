- This tree has it: `media_request_mark_manual_completion()` in
  `include/media/media-request.h` and `media_request_manual_complete()` in
  `drivers/media/mc/mc-request.c`.
- `media_request_mark_manual_completion()`: a plain store to
  `req->manual_completion`, no lock, no state check.
- Call it in the `req_queue` op before the objects are queued, as
  `vicodec_request_queue()` does; `media_request_clean()` clears the flag, so
  it has to be set again on every queue.
- With the flag set, `media_request_object_complete()` and
  `media_request_object_unbind()` still count down but leave the request
  QUEUED at zero.
- `media_request_manual_complete()` returns after a `WARN_ON_ONCE()` if `req`
  is NULL, the flag is clear, or the state is not QUEUED; a second call
  therefore WARNs.
- `media_request_manual_complete()` with `num_incomplete_objects` non-zero:
  clears the flag, WARNs, does not complete; the request then completes
  automatically when the last object is completed or unbound.
- On success it sets COMPLETE, wakes `req->poll_wait` and drops the queue-time
  reference with `media_request_put()`.
- **Unsafe usage**: calling `media_request_manual_complete()` before every
  object of the request is completed or unbound.
  - Safe: return the buffer, then `v4l2_ctrl_request_complete()`, then
    `media_request_manual_complete()`, as `device_run()` in
    `drivers/media/test-drivers/vicodec/vicodec-core.c` does; the `WARN_ON()`
    on `req->num_incomplete_objects` defines the requirement.
