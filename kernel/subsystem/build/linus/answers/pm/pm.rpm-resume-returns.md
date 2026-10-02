- `-EAGAIN` from `rpm_resume()`: never produced by its own tests; it is a
  callback value, or `-EACCES` from a callback converted in `rpm_callback()`.
- `power.no_callbacks`: gives `1` through the parent shortcut, and `0` when
  it resumes without the shortcut; no branch of `rpm_resume()` produces
  `-EPERM`.
- Parent: the sync path calls `rpm_resume(parent, 0)` when the parent has
  runtime PM enabled and `power.ignore_children` clear and the device is not
  `power.irq_safe`, and returns `-EBUSY` if the parent is not `RPM_ACTIVE`
  afterwards.
- `RPM_ASYNC`: leaves `rpm_resume()` before the parent step, so an async call
  never resumes the parent and never returns `-EBUSY`.
- Missing `->runtime_resume()`: `__rpm_callback()` skips a NULL callback and
  returns `0`; the status becomes `RPM_ACTIVE`.
- `-ENOSYS`: not produced by `drivers/base/power/runtime.c` for a missing
  callback.
- Supplier error: with `power.links_count > 0` and no `power.irq_safe`,
  `__rpm_callback()` returns the error of `rpm_get_suppliers()` and the
  callback is not run.
- `rpm_get_suppliers()`: ignores `-EACCES` from a supplier.
- Positive value from `->runtime_resume()`: `rpm_resume()` tests `if (retval)`,
  so the status goes back to `RPM_SUSPENDED` and the value is returned
  unchanged; a caller testing `< 0` reads it as success.
- Sync `0` with `RPM_TRANSPARENT`: can mean nothing was resumed; see "Calls
  while runtime PM is disabled".
- `-EINPROGRESS`: see "Concurrent transitions".
- Without `CONFIG_PM`: the stubs in `include/linux/pm_runtime.h` return `1`
  for `__pm_runtime_resume()` and `-ENOSYS` for `__pm_runtime_suspend()` and
  `__pm_runtime_idle()`.
