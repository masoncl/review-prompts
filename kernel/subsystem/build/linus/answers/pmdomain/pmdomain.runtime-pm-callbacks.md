- `suspend_ok`: called only when `pm_runtime_enabled(dev)`; with runtime PM
  disabled the governor check is skipped.
- Suspend, under the domain lock: `genpd_power_off()` runs first, then
  `genpd_drop_performance_state()`.
- Resume, under the domain lock: `genpd_restore_performance_state()` runs
  first, then `genpd_power_on()`.
- Provider `set_performance_state`: can be called while the domain is
  `GENPD_STATE_OFF`, because of that order; nothing on the path tests the
  status.
- IRQ-safe device in a domain without `GENPD_FLAG_IRQ_SAFE`: the domain lock,
  power-off, power-on and the performance-state drop and restore are all
  skipped; the device's vote stays in force while it is suspended.
- Same device: the governor check, the device callbacks and
  `genpd_stop_dev()` and `genpd_start_dev()` still run.
