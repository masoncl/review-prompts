- Outside `drivers/media/mc/mc-request.c`, in `.c` files only
  `drivers/media/common/videobuf2/videobuf2-core.c` and
  `drivers/media/v4l2-core/v4l2-ctrls-request.c` call bind, unbind or
  complete; drivers reach them through vb2 and the control helpers.
- `media_request_object_bind()`: accepts `MEDIA_REQUEST_STATE_UPDATING` and
  `MEDIA_REQUEST_STATE_QUEUED`; any other state is a WARN and `-EBUSY`.
- Bind in QUEUED exists for `v4l2_ctrl_request_complete()`, which adds a
  control object to a request that had none.
- `media_request_object_bind()`: takes no request reference and no object
  reference; the reference from `media_request_object_init()` belongs to the
  binding.
- Every in-tree `media_request_object_unbind()`, except the one inside
  `media_request_object_release()`, is followed by
  `media_request_object_put()` to drop that reference.
- `media_request_object_put()` dropping the last reference of a still-bound
  object: `WARN_ON()`, then it unbinds.
- `media_request_object_complete()` on an already completed object: returns
  silently, no WARN.
- `media_request_object_complete()`: dereferences `obj->req` without a NULL
  check, so an unbound object oopses.
- `media_request_object_unbind()`: tests `obj->completed` only in CLEANING; in
  IDLE, UPDATING and QUEUED it decrements `num_incomplete_objects` without
  that test; in COMPLETE it leaves the count alone.
- **Unsafe usage**: unbinding an already completed object while the request
  is still QUEUED; the count drops twice and the request can complete early.
  - Safe: unbind without completing, as `vb2_buffer_done()` does for buffers.
  - Safe: complete and leave bound until `media_request_clean()` unbinds in
    CLEANING, as `v4l2_ctrl_request_complete()` does for controls.
- A request becomes COMPLETE in `media_request_object_complete()` or
  `media_request_object_unbind()` when it is QUEUED, the count reaches zero
  and `manual_completion` is clear; otherwise in
  `media_request_manual_complete()`.
- Completion calls `media_request_put()` for the queue-time reference in the
  caller's context; `vb2_core_qbuf()` holds an extra reference in
  `vb->request` until dequeue or cancel so that the put from
  `vb2_buffer_done()` is not the last one.
