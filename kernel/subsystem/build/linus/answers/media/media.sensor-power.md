- System PM handlers: a sensor driver should in general not implement them, per
  `Documentation/driver-api/media/camera-sensor.rst`; `ccs_pm_ops` and
  `imx219_pm_ops` hold only `SET_RUNTIME_PM_OPS()`.
- Streaming state: the driver must not track it to stop in a suspend handler
  and restart in resume; the bridge driver stops and restarts the pipeline
  through `.enable_streams()` and `.disable_streams()`.
- `.s_stream` in `struct v4l2_subdev_video_ops`: marked DEPRECATED in
  `include/media/v4l2-subdev.h`; a new driver implements `.enable_streams` and
  `.disable_streams` and sets `.s_stream` to `v4l2_subdev_s_stream_helper()`.
- Runtime PM must be enabled before `v4l2_async_register_subdev()`, since the
  sub-device is usable as soon as it is registered; see
  `Documentation/driver-api/media/v4l2-subdev.rst`.
- Runtime PM callbacks: may be left unimplemented when the driver handles no
  clocks, regulators or GPIOs, for example an ACPI-only driver.
- `pm_runtime_put_autosuspend()`: calls `pm_runtime_mark_last_busy()` itself; no
  separate call is needed before it.
- **Potentially unsafe usage**: in `s_ctrl`, dropping a reference after
  `pm_runtime_get_if_active()` or `pm_runtime_get_if_in_use()` whenever the
  result is non-zero.
  - Unsafe: with `CONFIG_PM`, when `s_ctrl` can run while runtime PM is
    disabled for the device; `pm_runtime_get_conditional()` returns `-EINVAL`
    and takes no reference, so the put drops a reference held elsewhere or
    makes `rpm_drop_usage_count()` warn of an underflow.
  - Safe: skip the write on 0, write on any non-zero result, and put only when
    the result is > 0, as `ccs_set_ctrl()` does.
  - Safe: an unconditional put when `s_ctrl` cannot run while runtime PM is
    disabled, as `imx219_set_ctrl()`; `imx219_probe()` calls
    `pm_runtime_enable()` before it registers the sub-device and sets no
    control before that, and `imx219_remove()` frees the handler before
    `pm_runtime_disable()`.
