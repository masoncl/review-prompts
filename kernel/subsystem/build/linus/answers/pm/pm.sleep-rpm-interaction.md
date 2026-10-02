- `device_suspend_late()` in `drivers/base/power/main.c`: disables with
  `pm_runtime_disable()`, which passes `check_resume` true to
  `__pm_runtime_disable()`; it does not pass false.
- Resume request pending at that disable: carried out synchronously by
  `rpm_resume()` before runtime PM is disabled; it is not cancelled or lost.
- Pending idle, suspend or autosuspend request at that disable: cancelled by
  `__pm_runtime_barrier()`.
- `device_suspend()`: calls `pm_runtime_barrier()` before the callback, which
  also runs a pending resume request synchronously.
- `power.direct_complete` device: when the status is `RPM_SUSPENDED`,
  `device_suspend()` calls `pm_runtime_disable()` and, if the status is still
  `RPM_SUSPENDED`, the later suspend and resume phases run no callback;
  `device_resume()` does the matching `pm_runtime_enable()`.
- `pm_runtime_get_sync()` in a late, noirq or early callback, with
  `power.runtime_error` clear: returns 1 with no callback run when
  `power.runtime_status` and `power.last_status` are both `RPM_ACTIVE`, that
  is when the device was active at the disable and its status has not been
  changed since; otherwise `-EACCES`.
- Usage count on that `-EACCES`: already incremented by
  `__pm_runtime_resume()`; `pm_runtime_resume_and_get()` drops it again,
  `pm_runtime_get_sync()` does not.
