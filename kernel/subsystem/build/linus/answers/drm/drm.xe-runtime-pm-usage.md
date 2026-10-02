- `xe_pm_runtime_resume_and_get()`: returns bool; false means no reference
  is held.
- `xe_pm_runtime_get_ioctl()`: returns int, negative on failure; on the
  normal path it is `pm_runtime_get_sync()`, which raises the count even
  on failure.
- `xe_pm_runtime_get_noresume()`: takes the reference even when it warns
  "Missing outer runtime PM protection", so a put is always owed.
- Callback-task tracking (`xe->pm_callback_task`, written at entry and
  exit of `xe_pm_runtime_suspend()` and `xe_pm_runtime_resume()`) is
  unconditional, not debug-only.

| Scope-based form | Wraps |
|---|---|
| `guard(xe_pm_runtime)(xe)` | `xe_pm_runtime_get()` |
| `guard(xe_pm_runtime_noresume)(xe)` | `xe_pm_runtime_get_noresume()` |
| `ACQUIRE(xe_pm_runtime_ioctl, pm)(xe)` | `xe_pm_runtime_get_ioctl()`; test `ACQUIRE_ERR(xe_pm_runtime_ioctl, &pm)` |
| `guard(xe_pm_runtime_release_only)(xe)` | put only; get was done elsewhere |

- `scoped_guard()` works with the `guard()` forms; see
  `scoped_guard(xe_pm_runtime, xe)` in `xe_guc_submit.c`.
- No scope-based form exists for `xe_pm_runtime_get_if_active()`,
  `xe_pm_runtime_get_if_in_use()` or `xe_pm_runtime_resume_and_get()`.
- **Potentially unsafe usage**: taking a runtime PM reference in code
  reached from `xe_pm_runtime_suspend()` or `xe_pm_runtime_resume()`.
  - Unsafe: `xe_pm_runtime_get_ioctl()`; on the callback task it WARNs and
    returns `-ELOOP` without taking a reference.
  - Unsafe: relying on `xe_pm_runtime_get_if_active()`; it has no
    callback-task test and returns false while the status is not
    `RPM_ACTIVE`.
  - Unsafe: from another task the callback waits for; only
    `current == xe->pm_callback_task` is treated as inside the callback,
    any other task goes on to `pm_runtime_resume()`.
  - Unsafe: calling `pm_runtime_get_sync()` or `pm_runtime_resume()`
    directly; that bypasses the callback-task test. All such calls in xe
    are inside `xe_pm.c`.
  - Safe: `xe_pm_runtime_get()`, `xe_pm_runtime_get_if_in_use()`,
    `xe_pm_runtime_get_noresume()` and `xe_pm_runtime_resume_and_get()` on
    the callback task; each tests `xe_pm_read_callback_task(xe) == current`
    and only raises the count, and `xe_pm_runtime_put()` then uses
    `pm_runtime_put_noidle()`. `xe_bo_move()` relies on this when
    `xe_bo_evict_all()` runs from `xe_pm_runtime_suspend()`.
  - Safe: work that must run while a callback is in progress pairs
    `xe_pm_runtime_get_if_active()` with a
    `xe_pm_read_callback_task(xe) == NULL` test and puts only if the get
    succeeded, as `receive_g2h()` in `xe_guc_ct.c` does.
