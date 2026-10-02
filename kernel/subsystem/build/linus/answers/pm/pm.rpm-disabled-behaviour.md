- `RPM_TRANSPARENT`: defined in `include/linux/pm_runtime.h`; with it,
  `rpm_resume()` on a disabled device returns `0` where it would return
  `-EACCES`.
- Order in `rpm_resume()`: `power.runtime_error` (`-EINVAL`), then the `1`
  case (`power.runtime_status` and `power.last_status` both `RPM_ACTIVE`),
  then `RPM_TRANSPARENT`, then `-EACCES`.
- `0` from `RPM_TRANSPARENT`: nothing was resumed and the status is unchanged,
  so the device may be `RPM_SUSPENDED`.
- `pm_runtime_get_active()`: the only in-tree code that passes
  `RPM_TRANSPARENT`, for the guard classes `pm_runtime_active_try` and
  `pm_runtime_active_auto_try`.
- `pm_runtime_resume_and_get()`, `PM_RUNTIME_ACQUIRE_IF_ENABLED()` and
  `PM_RUNTIME_ACQUIRE_IF_ENABLED_AUTOSUSPEND()`: pass no `RPM_TRANSPARENT`
  and fail with `-EACCES` on a disabled device outside the `1` case, or with
  `-EINVAL` when `power.runtime_error` is set.
- `rpm_suspend()` and `rpm_idle()`: do not test `RPM_TRANSPARENT`; a disabled
  device gets `-EACCES` from `rpm_check_suspend_allowed()` whatever the flags,
  unless `power.runtime_error` is set, which gives `-EINVAL` first.
