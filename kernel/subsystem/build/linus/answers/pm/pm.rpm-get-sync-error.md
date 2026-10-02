- Runtime PM disabled: `rpm_resume()` returns 1, not `-EACCES`, when
  `runtime_status` and `last_status` are both `RPM_ACTIVE`; then
  `pm_runtime_get_sync()` returns 1 and `pm_runtime_resume_and_get()`
  returns 0, each holding a reference.
- `pm_runtime_get_sync()` success is `>= 0`: 1 when the device was already
  active, and always 1 with `CONFIG_PM` off; `pm_runtime_resume_and_get()`
  returns only 0 or a negative errno.
- `pm_runtime_get()`: `-EINPROGRESS` means a resume is already running
  (`RPM_RESUMING`); the reference is held as for every other result.
- A put after a failed `pm_runtime_resume_and_get()`: see "Counter-only
  helpers" for what each put does at zero.
