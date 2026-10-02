- **Potentially unsafe usage**: `pm_runtime_put_sync()` dropping the last
  reference just before `pm_runtime_disable()` where the device must end up
  suspended.
  - Unsafe: while `use_autosuspend` is set and the delay has not expired;
    `rpm_idle()` adds `RPM_AUTO`, `rpm_suspend()` only arms the timer, and
    `__pm_runtime_barrier()` then cancels it, leaving the device active.
  - Safe: after `pm_runtime_dont_use_autosuspend()`, as `omap_i2c_remove()`
    in `drivers/i2c/busses/i2c-omap.c` does;
    `pm_runtime_autosuspend_expiration()` then returns 0.
  - Safe: with `pm_runtime_put_sync_suspend()` instead, as `hidma_remove()`
    in `drivers/dma/qcom/hidma.c` does; it passes no `RPM_AUTO`, see "Wrapper
    to base function map".
  - Safe: where the status is tested after the disable and power is cut by
    hand, as `ov5675_remove()` in `drivers/media/i2c/ov5675.c` does with
    `pm_runtime_status_suspended()` and `pm_runtime_set_suspended()`.
- `pm_runtime_dont_use_autosuspend()` with runtime PM enabled: ends in a
  synchronous `rpm_idle(dev, RPM_AUTO)`, so with a zero counter it can run
  the `runtime_suspend` callback in the caller.
- That `rpm_idle()` returns `-EAGAIN` and does nothing while a suspend,
  autosuspend or resume request is still queued.
- `__device_release_driver()` in `drivers/base/dd.c`: calls
  `pm_runtime_put_sync()` before `device_remove()`, so the remove callback
  runs with no reference held by the driver core.
- `__pm_runtime_disable()`: with `check_resume` true, as
  `pm_runtime_disable()` passes, runs a pending `RPM_REQ_RESUME` before it
  raises `disable_depth`; when `disable_depth` is already non-zero it only
  increments and calls no barrier.
- `__pm_runtime_barrier()`: stops the timer through
  `pm_runtime_deactivate_timer()`, which uses `hrtimer_try_to_cancel()`;
  calls `cancel_work_sync()` only when `dev->power.request_pending` is set.
- `pm_runtime_force_suspend()`: calls `pm_runtime_disable()` itself and
  returns with runtime PM still disabled on success, so a further
  `pm_runtime_disable()` raises `disable_depth` to 2.
- `pm_runtime_reinit()`: does not lower `disable_depth` on unbind.
