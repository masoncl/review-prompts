- `RPM_GET_PUT`: `__pm_runtime_suspend()` calls `rpm_drop_usage_count()`, not
  `atomic_dec_and_test()`.
- `rpm_drop_usage_count()` on underflow: increments the counter back, warns
  and returns `-EINVAL`; `rpm_suspend()` is not called.
- `rpm_check_suspend_allowed()`: one else-if chain; see it for the order.
- `power.child_count` non-zero without `power.ignore_children`: `-EBUSY`, not
  `-EAGAIN`.
- `__dev_pm_qos_resume_latency()` equal to 0: `-EPERM`.
- `1` (already `RPM_SUSPENDED`): tested last, so a suspended device with a
  held reference gets `-EAGAIN`.
- `1`: returned for `RPM_ASYNC` and `RPM_AUTO` calls too.
- `RPM_RESUMING`: not tested by `rpm_check_suspend_allowed()`; `rpm_suspend()`
  tests it and returns `-EAGAIN` only without `RPM_ASYNC`.
- `RPM_AUTO` with an unexpired delay: returns `0`, not `-EAGAIN`.
- Autosuspend timer: armed in that branch whether or not `RPM_ASYNC` is set.
- `RPM_SUSPENDING` with `RPM_ASYNC` or `RPM_NOWAIT`: `-EINPROGRESS`, not
  `-EBUSY`.
- `RPM_ASYNC` request queued on `pm_wq`: returns `0`, not `-EINPROGRESS`.
- `-EAGAIN` after a successful callback: `power.deferred_resume` was set; see
  "Concurrent transitions".
