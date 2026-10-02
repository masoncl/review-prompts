- `v4l2_ctrl_handler_free()`: returns `int`, the handler's `hdl->error`; returns
  0 when `hdl` is NULL.
- `v4l2_ctrl_handler_free()` early return: tests `hdl->buckets`, not a mutex
  field; with `hdl->buckets` NULL (failed init, zeroed handler, second call) it
  returns `hdl->error` without taking the lock.
- `hdl->error` after free: unchanged; free never clears it, so a second call
  returns the same error.
- `handler_set_err()`: has no benign error codes; it stores any error while
  `hdl->error` is 0.
- `v4l2_ctrl_new_fwnode_properties()`: returns `int` (`hdl->error`), not a
  control pointer.
- Control ID already in the handler (owned or inherited): not reported.
  `handler_new_ref()` drops the new ref and returns 0, so `v4l2_ctrl_new()`
  links the control on `hdl->ctrls` and returns it non-NULL with `hdl->error`
  still 0.
- Such a duplicate control: has no ref and `ctrl->cluster` stays NULL;
  `__v4l2_ctrl_handler_setup()` reads `ctrl->cluster[0]` for every control on
  `hdl->ctrls`.
