- Already `RPM_SUSPENDED`, with `RPM_GET_PUT`: `rpm_idle()` returns `1`, as
  `pm_runtime_put_sync()` does.
- Already `RPM_SUSPENDED`, without `RPM_GET_PUT`: `-EAGAIN`, as
  `pm_runtime_idle()` and `pm_request_idle()` do.
- `drivers/base/power/runtime-test.c`: `pm_runtime_already_suspended_test()`
  and `pm_runtime_idle_test()` pin both results.
- Usage counter: with `RPM_GET_PUT`, decremented by `rpm_drop_usage_count()`
  in `__pm_runtime_idle()` before `rpm_idle()` runs; `rpm_idle()` never
  changes it.
- Underflow: `__pm_runtime_idle()` returns `-EINVAL` without calling
  `rpm_idle()`.
- `-EINPROGRESS`: `power.idle_notification` is already set; it never means
  "queued".
- `RPM_ASYNC` with an idle callback: queues `RPM_REQ_IDLE` and returns `0`.
- `RPM_ASYNC` with no idle callback, or with `power.no_callbacks`: nothing is
  queued as `RPM_REQ_IDLE`; the result is that of
  `rpm_suspend(dev, rpmflags | RPM_AUTO)`.
- Idle callback: called as `callback(dev)`, not through `__rpm_callback()` or
  `rpm_callback()`, so `-EACCES` from it is returned unchanged.
