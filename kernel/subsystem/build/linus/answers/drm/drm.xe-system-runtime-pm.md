- `xe->d3cold.capable`: set in `xe_pm_probe()`, which `xe_pci_probe()` calls
  before `xe_device_probe()`; `xe_pm_init()` only reads it.
- `xe->d3cold.allowed`: written only by `xe_pm_d3cold_allowed_toggle()`,
  called only from `xe_pci_runtime_idle()`.
- `xe_pm_d3cold_allowed_toggle()`: inputs are `capable` and total VRAM in
  use below `xe->d3cold.vram_threshold`; it reads no other setting.

| Path | reads `allowed` | reads `capable` |
|---|---|---|
| `xe_pm_suspend()`, `xe_pm_resume()` | no | not in the function body |
| `xe_pci_suspend()`, `xe_pci_resume()` | no | yes, in `d3cold_toggle()` |
| `xe_pm_runtime_suspend()`, `xe_pm_runtime_resume()` | yes | in the function body, only to pick the lockdep map, via `xe_rpm_reclaim_safe()` |
| `xe_pci_runtime_suspend()` | yes | yes, in `d3cold_toggle()` |
| `xe_pci_runtime_resume()` | yes | not in the function body |

- `display/xe_display.c`: `xe_display_pm_runtime_suspend()`,
  `xe_display_pm_runtime_suspend_late()`,
  `xe_display_pm_runtime_resume_early()` and
  `xe_display_pm_runtime_resume()` also branch on `allowed`.
- Runtime path with `allowed` false: calls `xe_gt_runtime_suspend()` and
  `xe_gt_runtime_resume()`; with `allowed` true it calls `xe_gt_suspend()`
  and `xe_gt_resume()`, as the system path does.
- `xe_rpm_reclaim_safe()`: returns `!xe->d3cold.capable`; it selects which
  lockdep map the runtime callbacks and the getters acquire.
