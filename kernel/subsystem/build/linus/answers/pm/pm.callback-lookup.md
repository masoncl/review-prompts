- `__rpm_get_callback()`: falls back to `__rpm_get_driver_callback()` whenever
  the member read from the selected ops is NULL, not only when no ops was
  selected.
- `device_suspend()`: the pm_domain, type and class branches all `goto Run`,
  where a NULL `callback` is replaced by `pm_op(dev->driver->pm, state)`.
- `device_suspend()`: the legacy bus branch is the only one that skips the
  driver lookup.
- Legacy bus `suspend`: tested before the driver, not after; when
  it is taken, `dev->driver->pm` is not consulted even if set.
- legacy_resume(): not in this tree; `device_resume()` puts
  `dev->bus->resume` in `callback` and runs it through `dpm_run_callback()`.
- Legacy bus `resume` in `device_resume()`: chosen without `pm_op()`, so it
  runs for every `state.event`.
- `struct class` and `struct device_type`: have a `pm` pointer only, no legacy
  `suspend` or `resume`; the "bus or class" in the `legacy_suspend()` kerneldoc
  has no class caller.
- `suspend` and `resume` in `struct device_driver`: `drivers/base/power/` never
  calls them; `device_pm_check_callbacks()` only tests them for
  `power.no_pm_callbacks`.
- NULL `runtime_idle` in `rpm_idle()`: treated as success, and `rpm_idle()`
  goes on to `rpm_suspend()` with `RPM_AUTO`.
- `pm_runtime_force_suspend()` and `pm_runtime_force_resume()`: look up through
  `get_callback()`, not `RPM_GET_CALLBACK()`.
