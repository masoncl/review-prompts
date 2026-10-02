- Skipped controls: `ctrl->done`, `V4L2_CTRL_TYPE_BUTTON`,
  `V4L2_CTRL_FLAG_READ_ONLY`. Volatile controls and controls without `s_ctrl`
  are not skipped; `call_op()` returns 0 when the op is missing.
- Skip test: applies to the control being walked, not to its master, so a
  cluster with a read-only master is still applied when the walk reaches a
  writable member.
- `__v4l2_ctrl_handler_setup()`: calls `s_ctrl` directly; it does not go
  through `try_or_set_cluster()`, so no `try_ctrl`, no `cluster_changed()` and
  no `new_to_cur()`. No event is sent and `has_changed` keeps its old value.
- `Documentation/driver-api/media/camera-sensor.rst`: says
  `v4l2_ctrl_handler_setup()` may not be used in the `runtime_resume`
  callback, and names `pm_runtime_get_if_active()` for `s_ctrl`.
- `pm_runtime_get_if_active()` and `pm_runtime_get_if_in_use()`: both return
  `-EINVAL` when runtime PM is disabled, else 0 when the status is not
  `RPM_ACTIVE`; see `pm_runtime_get_conditional()` in
  `drivers/base/power/runtime.c`.
- There is no imx219_start_streaming() here; `imx219_enable_streams()` in
  `drivers/media/i2c/imx219.c` does that.
- **Potentially unsafe usage**: applying the controls from a `runtime_resume`
  callback.
  - Unsafe: when `s_ctrl` gates register writes on
    `pm_runtime_get_if_in_use()` or `pm_runtime_get_if_active()`; the status
    is `RPM_RESUMING` during the callback, so the get returns 0 and `s_ctrl`
    skips the write.
  - Unsafe: when the callback takes `hdl->lock` and the resume can be
    triggered by a task that already holds it, such as an op or a stream op
    under a shared `sd->state_lock`.
  - Safe: from the stream-start path after `pm_runtime_resume_and_get()` has
    returned, with `__v4l2_ctrl_handler_setup()` under the held lock, as
    `imx219_enable_streams()` does.
  - Safe: in the callback when `s_ctrl` tests `pm_runtime_suspended()`, which
    is false in `RPM_RESUMING`, and no caller resumes the device with the
    handler lock held, as `ov8865_resume()` with `ov8865_s_ctrl()`.
