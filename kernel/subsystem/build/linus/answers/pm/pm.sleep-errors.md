- `resume_event()`:

| Suspend event | Message returned |
|---|---|
| `PM_EVENT_SUSPEND` | `PMSG_RESUME` |
| `PM_EVENT_FREEZE`, `PM_EVENT_QUIESCE` | `PMSG_RECOVER` |
| `PM_EVENT_HIBERNATE` | `PMSG_RESTORE` |
| any other, for example `PM_EVENT_POWEROFF` | `PMSG_ON` |

- `PMSG_ON`: `pm_op()`, `pm_late_early_op()` and `pm_noirq_op()` return NULL
  for it, so the noirq and early rollback runs no callback; the flags are
  still cleared and runtime PM is re-enabled.
- Who rolls back:

| Failing function | Rolls back itself | Left to the caller |
|---|---|---|
| `dpm_suspend_noirq()` | `dpm_resume_noirq(resume_event(state))` | early resume and later |
| `dpm_suspend_late()` | `dpm_resume_early(resume_event(state))` | `dpm_resume_end()` |
| `dpm_suspend_end()` | as above, plus `dpm_resume_early()` after a noirq failure | `dpm_resume_end()` |
| `dpm_suspend()`, `dpm_prepare()` | nothing | everything |

- Caller's message for `dpm_resume_end()`: `PMSG_RESUME` in
  `suspend_devices_and_enter()`, `PMSG_RECOVER` in `hibernation_restore()`,
  `PMSG_RESTORE` in `hibernation_platform_enter()`.
- Devices walked: every device of the phase, since the suspend loop splices
  the devices it did not reach onto the target list.
- Devices resumed: only those whose flag for the phase is set; the failing
  device's flag stays clear, so its resume callback for that phase is not
  called.
- `-EAGAIN` from prepare: `dpm_prepare()` clears the error but leaves the
  device at the head of `dpm_list`, so the next iteration calls
  `device_prepare()` on the same device again.
