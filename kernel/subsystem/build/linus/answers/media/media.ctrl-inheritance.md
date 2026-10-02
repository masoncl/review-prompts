- Private controls: the test is `ctrl->is_private`, not the ID.
  `v4l2_ctrl_new()` rejects an ID at or above `V4L2_CID_PRIVATE_BASE` with
  `-ERANGE`.
- `V4L2_CTRL_TYPE_CTRL_CLASS` controls: skipped; `handler_new_ref()` creates
  the class control in the target handler itself when the control it adds is
  not a compound type.
- `v4l2_ctrl_add_handler()`: walks `add->ctrl_refs`, so controls that `add`
  itself inherited are passed on; `ctrl->handler` stays the original owner.
- `from_other_dev`: stored as the caller passed it; nothing compares devices.
  Only `v4l2_ctrl_request_clone()` reads it: such refs are left out of request
  handler objects, so those controls cannot be set through a request.
- Reference counting: none. `v4l2_device_unregister_subdev()` leaves the refs
  in `v4l2_dev->ctrl_handler` in place.
- **Potentially unsafe usage**: freeing a handler whose controls another
  handler still references.
  - Unsafe: while the other handler can still be looked up or added to;
    `find_ref()` and `handler_new_ref()` read `ref->ctrl->id` of the freed
    control.
  - Safe: when no lookup can follow, in either free order, because
    `v4l2_ctrl_handler_free()` does not read `ref->ctrl`;
    `vivid_free_controls()` runs from `vivid_dev_release()`, the
    `struct v4l2_device` release callback.
