- `device_prepare()`: sets `power.direct_complete` from the event, the
  `->prepare()` return value or `power.no_pm_callbacks`, and
  `DPM_FLAG_NO_DIRECT_COMPLETE` only; the runtime PM status and
  `pm_runtime_enabled()` play no part in it.
- Runtime status: tested in `device_suspend()` with
  `pm_runtime_status_suspended()`, which ignores the disable depth, so a
  device with runtime PM disabled and status `RPM_SUSPENDED` qualifies.
- There is no __device_suspend() here; `device_suspend()` does that job.
- `device_suspend()` also clears the flag when `device_may_wakeup()` or
  `device_wakeup_path()` is true.
- Parent and suppliers: cleared only by
  `dpm_clear_superiors_direct_complete()`, called from the child's
  `device_suspend()` after its callback returned 0 or it had none;
  `device_prepare()` and `dpm_prepare()` clear nothing in the parent.
- `dpm_clear_superiors_direct_complete()`: clears every supplier, without
  looking at link flags or link status.
- `dpm_clear_superiors_direct_complete()` is not called for a child that
  direct-completes itself, is `power.syscore`, or left early on
  `async_error` or a pending wakeup.
- Late and early phases: `device_suspend_late()` and `device_resume_early()`
  test `power.direct_complete` alone and leave before touching runtime PM;
  only the two noirq functions test `power.syscore || power.direct_complete`.
- `device_resume()`: reaches its direct-complete branch only when
  `power.is_suspended` is set, and does not wait for the parent or suppliers
  there.
