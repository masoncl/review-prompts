- Clearing: `device_unbind_cleanup()` in `drivers/base/dd.c` calls
  `dev_pm_set_driver_flags(dev, 0)`; it runs on unbind and on probe failure,
  so a driver need not clear the flags itself.

| Flag | Tested by | Easy to miss |
|---|---|---|
| `DPM_FLAG_NO_DIRECT_COMPLETE` | `device_prepare()` | — |
| `DPM_FLAG_SMART_PREPARE` | `pci_pm_prepare()`, `acpi_subsys_prepare()` only | the PM core never tests it |
| `DPM_FLAG_SMART_SUSPEND` | `device_prepare_smart_suspend()` only | all other code reads `dev_pm_smart_suspend()` |
| `DPM_FLAG_MAY_SKIP_RESUME` | `device_suspend()`, `device_suspend_noirq()` | covers noirq and early resume only |

- `DPM_FLAG_SMART_PREPARE`: the only effect is that a driver `->prepare()`
  returning 0 makes the bus type return 0.
- `DPM_FLAG_SMART_PREPARE` with a positive driver return: the value is not
  passed through; `pci_pm_prepare()` still applies `pci_dev_need_resume()`
  and `acpi_subsys_prepare()` still applies `acpi_dev_needs_resume()`.
- `DPM_FLAG_SMART_SUSPEND`: `device_prepare_smart_suspend()` treats a device
  with `power.no_pm_callbacks` as if the flag were set, and has no wakeup
  test.
- `DPM_FLAG_MAY_SKIP_RESUME`: `device_resume()` makes no skip test, and
  `pci_pm_resume()` does not call `dev_pm_skip_resume()`, so the driver's
  `->resume()` runs even when its noirq and early resume were skipped.
