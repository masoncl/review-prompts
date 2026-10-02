- `pm_runtime_put()`: returns `void` in `include/linux/pm_runtime.h`; code
  that assigns or tests its result, or returns it from a function that is
  not `void`, does not compile.
- `__pm_runtime_put_autosuspend()`: returns `int`, like
  `pm_runtime_put_autosuspend()`.
- `Documentation/power/runtime_pm.rst`: still lists `int pm_runtime_put()`
  "and return its result"; the header is what compiles.
- Result 1: the status was already `RPM_SUSPENDED`; it comes from
  `rpm_check_suspend_allowed()`.
- `CONFIG_PM` off: the puts that return `int`, for example
  `pm_runtime_put_sync()` and `pm_runtime_put_autosuspend()`, return
  `-ENOSYS` from the stubs of `__pm_runtime_idle()` and
  `__pm_runtime_suspend()`, so a caller that propagates the result fails on
  such a kernel.
- `pm_runtime_put_sync()`: also returns any non-zero value of the
  `runtime_idle` callback, unchanged; see `rpm_idle()`.
- Synchronous puts: return the error of the `runtime_suspend` callback, with
  `-EACCES` turned into `-EAGAIN` by `rpm_callback()`; unless the result is
  `-EAGAIN` or `-EBUSY`, `rpm_suspend()` stores it in
  `dev->power.runtime_error` and later calls return `-EINVAL`.
