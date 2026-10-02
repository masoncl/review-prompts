- `power.needs_force_resume`: set by `pm_runtime_force_suspend()` only when
  the callback succeeded and `pm_runtime_need_not_resume()` is false; a
  callback that ran for an unused device leaves it clear.
- Status while `power.needs_force_resume` is set: left untouched, so
  `RPM_ACTIVE` although the callback has suspended the hardware.
- Status when the callback succeeded and the flag stays clear:
  `pm_runtime_force_suspend()` calls `pm_runtime_set_suspended()`.
- `pm_runtime_force_suspend()` with the flag already set: returns 0 right
  after `pm_runtime_disable()` and runs no callback; the disable depth still
  goes up.
- `pm_runtime_force_resume()`: clears the flag and `power.smart_suspend` on
  every path, including a callback error.
- There is no pm_runtime_set_strict_midlayer() here; the accessors are
  `dev_pm_set_strict_midlayer()` and `dev_pm_strict_midlayer_is_set()` in
  `include/linux/device.h`.
- `power.strict_midlayer` effect: `get_callback()` in
  `drivers/base/power/runtime.c` returns only the callback from
  `dev->driver->pm`; there is no other test of middle-layer state.
- `power.strict_midlayer` is set in `pci_pm_prepare()` and
  `acpi_subsys_prepare()`, and cleared in `pci_pm_complete()` and
  `acpi_subsys_complete()`; `pci_pm_init()` does not set it.
- Flag clear, as it is for a device that reached neither prepare function
  and after `pci_pm_complete()` or `acpi_subsys_complete()`:
  `pm_runtime_force_suspend()` from a remove callback uses the normal lookup,
  middle layer first.
- Without `CONFIG_PM_SLEEP`: `dev_pm_set_strict_midlayer()` does nothing and
  `dev_pm_strict_midlayer_is_set()` returns false.
