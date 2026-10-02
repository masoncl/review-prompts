- Guard classes in `include/linux/pm_runtime.h`:

| Class | Entry | Exit | Acquire macro |
|---|---|---|---|
| `pm_runtime_noresume` | `pm_runtime_get_noresume()` | `pm_runtime_put_noidle()` | none |
| `pm_runtime_active` | `pm_runtime_get_sync()`, result dropped | `pm_runtime_put()` | none |
| `pm_runtime_active_auto` | `pm_runtime_get_sync()`, result dropped | `pm_runtime_put_autosuspend()` | none |
| `pm_runtime_active_try` | `pm_runtime_get_active()` with `RPM_TRANSPARENT` | `pm_runtime_put()` | `PM_RUNTIME_ACQUIRE()` |
| `pm_runtime_active_try_enabled` | `pm_runtime_resume_and_get()` | `pm_runtime_put()` | `PM_RUNTIME_ACQUIRE_IF_ENABLED()` |
| `pm_runtime_active_auto_try` | `pm_runtime_get_active()` with `RPM_TRANSPARENT` | `pm_runtime_put_autosuspend()` | `PM_RUNTIME_ACQUIRE_AUTOSUSPEND()` |
| `pm_runtime_active_auto_try_enabled` | `pm_runtime_resume_and_get()` | `pm_runtime_put_autosuspend()` | `PM_RUNTIME_ACQUIRE_IF_ENABLED_AUTOSUSPEND()` |

- `PM_RUNTIME_ACQUIRE_ERR()`: takes the address of the variable named in the
  acquire macro; it is defined on class `pm_runtime_active` and serves all
  four acquire macros; 0 on success, negative errno on failure.
- Failed conditional acquire: the reference is already dropped by
  `pm_runtime_get_active()` and the exit put is skipped.
- Runtime PM disabled, `_try` classes: `rpm_resume()` returns 0 without
  resuming, so the acquire succeeds and holds a reference while the device
  may be suspended.
- Runtime PM disabled, `_try_enabled` classes: `-EACCES`, except that they
  succeed when `runtime_status` and `last_status` are both `RPM_ACTIVE`.
- `last_status`: set by `__pm_runtime_disable()` to the status at that moment
  and reset to `RPM_INVALID` by `pm_runtime_enable()`, so `_try_enabled`
  fails before the first enable even after `pm_runtime_set_active()`.
- `dev->power.runtime_error` set: both kinds fail with `-EINVAL`, disabled or
  not; `rpm_resume()` tests it first.
- 0 from `PM_RUNTIME_ACQUIRE_ERR()`: for the `_try` classes it also covers
  "runtime PM disabled, nothing resumed, status possibly `RPM_SUSPENDED`";
  for the `_try_enabled` classes a disabled device gives 0 only in the
  both-`RPM_ACTIVE` case above.
- For example `acpi_tad_wake_set()` in `drivers/acpi/acpi_tad.c` uses
  `PM_RUNTIME_ACQUIRE()`; `sound/soc/codecs/cs42l43-jack.c` uses
  `PM_RUNTIME_ACQUIRE_IF_ENABLED_AUTOSUSPEND()`.
