- `power.runtime_error` is written with a callback result in one place: the
  `fail:` label of `rpm_suspend()`.
- `rpm_callback()`: does not touch `power.runtime_error`; it only converts
  `-EACCES` to `-EAGAIN`.
- `->runtime_resume()` failure: not recorded. `rpm_resume()` sets the status
  to `RPM_SUSPENDED` and returns the value; the next resume runs the callback
  again.
- `->runtime_suspend()` values recorded: every non-zero value other than
  `-EAGAIN`, `-EBUSY` and `-EACCES`, positive values included.
- Missing `->runtime_suspend()`: `__rpm_callback()` returns `0`; nothing is
  recorded and the status becomes `RPM_SUSPENDED`.
- `__pm_runtime_set_status()` with the field set: accepted while runtime PM is
  enabled; the device need not be disabled first.
- `__pm_runtime_set_status()` returning an error (parent not active, supplier
  activation failed): leaves the field set.
- `pm_runtime_init()`: zeroes the field.
- `pm_runtime_reinit()`: has no write of the field of its own; when the
  device is disabled and its status is `RPM_ACTIVE` it calls
  `pm_runtime_set_suspended()`, which clears the field.
- There is no pm_runtime_clean_up_links() in this tree.
