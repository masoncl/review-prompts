- `power.lock`: initialised by `device_pm_init_common()` in
  `drivers/base/power/power.h`, not by `pm_runtime_init()`.
- `pm_runtime_init()`: sets `power.runtime_auto` to true and clears
  `power.needs_force_resume`.
- `pm_runtime_init()`: does not write `irq_safe`, `no_callbacks`,
  `use_autosuspend`, `autosuspend_delay`, `last_busy` or `links_count`.
- `pm_runtime_active()`: true for every device with `disable_depth` non-zero,
  so true for a new device whose status is `RPM_SUSPENDED`.
- `pm_runtime_suspended()`: false for a disabled device;
  `pm_runtime_status_suspended()` ignores `disable_depth`.

| Member | Written | Read |
|---|---|---|
| `ignore_children` | plain store, no lock, in `pm_suspend_ignore_children()` | under the lock in `rpm_check_suspend_allowed()`; the parent's flag is read holding only the child's lock in `rpm_suspend()` |
| `no_callbacks` | under the lock in `pm_runtime_no_callbacks()`; plain store in `device_set_pm_not_required()` | under the lock in `rpm_idle()`, `rpm_suspend()` and `rpm_resume()` |
| `autosuspend_delay` | under the lock in `pm_runtime_set_autosuspend_delay()` | `READ_ONCE()`, lock not needed, in `pm_runtime_autosuspend_expiration()` |
| `last_busy` | `WRITE_ONCE()`, no lock | `READ_ONCE()`, no lock |
| `irq_safe` | under the lock | without the lock in the `might_sleep_if()` checks and `__rpm_callback()` |
| `last_status` | under the lock, except in `pm_runtime_init()` | without the lock in `pm_runtime_blocked()` |

- `child_count` of the parent: `rpm_suspend()`, the normal path of
  `rpm_resume()` and the `RPM_SUSPENDED` branch of
  `__pm_runtime_set_status()` change it holding only the child's
  `power.lock`.
- `child_count` under the parent's lock: only the `no_callbacks` shortcut in
  `rpm_resume()` and the `RPM_ACTIVE` branch of `__pm_runtime_set_status()`.
- `disable_depth`: a 3-bit field; `__pm_runtime_disable()` increments it with
  no range check, so an eighth nested disable wraps it to 0.
- `disable_depth`: `__pm_runtime_set_status()` also increments it, under the
  lock, and ends with `pm_runtime_enable()`.
- `usage_count`: `pm_runtime_forbid()` holds one count until
  `pm_runtime_allow()`; `update_autosuspend()` holds one while
  `use_autosuspend` is set and the delay is negative.
- `pm_runtime_get_noresume()`: does not stop a suspend that has passed
  `rpm_check_suspend_allowed()`; `rpm_suspend()` tests `usage_count` there,
  under the lock, and not again after the callback succeeds.
- `pm_runtime_get_if_active()` and `pm_runtime_get_if_in_use()`: return
  `-EINVAL` with the count unchanged when `disable_depth` is non-zero; only a
  return of 1 means a count is held.
- **Potentially unsafe usage**: testing `power.runtime_status` without
  `power.lock` and acting on the result.
  - Unsafe: with runtime PM enabled, while another task can start a suspend
    or resume; a count taken with `pm_runtime_get_noresume()` just before the
    test does not prevent it.
  - Safe: with `power.lock` held across the test and the action, as
    `pci_dev_adjust_pme()` in `drivers/pci/pci.c` does; every caller of
    `__update_runtime_status()` holds the lock.
  - Safe: `pm_runtime_get_if_active()`, which tests the status and takes the
    count in one hold of the lock.
  - Safe: after `pm_runtime_disable()`, while nothing calls
    `__pm_runtime_set_status()`, as `pm_runtime_force_suspend()` does with
    `pm_runtime_status_suspended()`; `rpm_resume()` and
    `rpm_check_suspend_allowed()` return on `disable_depth` above 0 before
    any status write.
- **Potentially unsafe usage**: writing `power.disable_depth` directly.
  - Unsafe: without `power.lock` on a device other tasks can reach, or as the
    0 -> 1 step while `runtime_error` is clear; at depth 0 -> 1
    `__pm_runtime_disable()` runs `__pm_runtime_barrier()` and sets
    `last_status`, which a direct write skips.
  - Safe: `pm_runtime_disable()` and `pm_runtime_enable()` instead.
  - Safe: under `power.lock` when the depth is already non-zero or
    `runtime_error` is set, undone by `pm_runtime_enable()`, as
    `__pm_runtime_set_status()` does; with `runtime_error` set `rpm_resume()`
    and `rpm_check_suspend_allowed()` return `-EINVAL` first.
  - Safe: the plain store in `pm_runtime_init()`, which `device_initialize()`
    reaches through `device_pm_init()` before the device is registered.
