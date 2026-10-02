| Value | Stands for | `power.runtime_status` | `power.last_status` |
|---|---|---|---|
| `RPM_INVALID` | no saved status: runtime PM is enabled, or was never enabled | never | yes |
| `RPM_BLOCKED` | device was disabled and never enabled when `device_prepare()` ran; enabling it now warns | never | yes |
| `RPM_ACTIVE`, `RPM_SUSPENDED` | settled state | yes | yes, copied at disable |
| `RPM_RESUMING`, `RPM_SUSPENDING` | callback in progress | yes | never |

- `__pm_runtime_disable()`: runs `__pm_runtime_barrier()` before it copies
  `runtime_status` into `last_status`, so a transient value is never copied.
- `pm_runtime_enable()` when the depth reaches 0: sets `last_status` to
  `RPM_INVALID`; it does not restore `runtime_status` from it.
- `rpm_resume()` does not test `RPM_BLOCKED`; there is no `-EPERM` for it.
- `RPM_BLOCKED` readers: `pm_runtime_enable()`, `pm_runtime_unblock()` and
  `pm_runtime_blocked()`, which `device_prepare_smart_suspend()` in
  `drivers/base/power/main.c` calls.
- `__pm_runtime_set_status()` on a disabled device: writes `runtime_status`,
  not `last_status`; after `pm_runtime_set_active()` on a never-enabled device
  `last_status` is still `RPM_INVALID` and `rpm_resume()` returns `-EACCES`.
