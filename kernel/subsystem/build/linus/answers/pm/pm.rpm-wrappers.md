- Last-busy refresh by the `RPM_AUTO` wrappers:

| Wrapper | Calls `pm_runtime_mark_last_busy()` itself |
|---|---|
| `pm_runtime_autosuspend()` | yes |
| `pm_request_autosuspend()` | yes |
| `pm_runtime_put_autosuspend()` | yes |
| `pm_runtime_put_sync_autosuspend()` | yes |
| `__pm_runtime_put_autosuspend()` | no |

- `__pm_runtime_put_autosuspend()`: defined in `include/linux/pm_runtime.h`;
  same flags as `pm_runtime_put_autosuspend()`, which calls it.
- Wrappers that reach `__pm_runtime_idle()` (`pm_runtime_idle()`,
  `pm_request_idle()`, `pm_runtime_put()`, `pm_runtime_put_sync()`): honour
  the autosuspend delay although they pass no `RPM_AUTO`, because `rpm_idle()`
  ends with `rpm_suspend(dev, rpmflags | RPM_AUTO)`.
- `pm_runtime_suspend()` and `pm_runtime_put_sync_suspend()`: the two wrappers
  that reach `rpm_suspend()` without `RPM_AUTO`, so they ignore the delay.
- `pm_runtime_autosuspend()` and `pm_runtime_put_sync_autosuspend()`: have no
  `RPM_ASYNC`, but they refresh last-busy first, so with autosuspend in use
  and a positive delay `rpm_suspend()` arms `dev->power.suspend_timer` and
  returns 0 instead of running the `runtime_suspend` callback in the caller.
