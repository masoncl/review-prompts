- `GENPD_FLAG_RPM_ALWAYS_ON`: the one flag the core sets. `pm_genpd_init()` ORs
  it in when `gov` is `&pm_domain_always_on_gov`, before the always-on check, so
  that governor with `is_off` true returns `-EINVAL`.
- `GENPD_FLAG_NO_SYNC_STATE`: tested only when the provider node has no
  `struct device`, in `of_genpd_add_provider_simple()` and
  `of_genpd_add_provider_onecell()`. `genpd->sync_state` then stays
  `GENPD_SYNC_STATE_OFF` and, unless another domain of the same onecell node
  carries the callback, the provider has to call `of_genpd_sync_state()`
  itself to clear `stay_on`, as `drivers/soc/tegra/pmc.c` does.
- `GENPD_FLAG_IRQ_SAFE` changes runtime power-off: without it, each attached
  device with `pm_runtime_is_irq_safe()` is counted as not suspended in
  `genpd_power_off()`, and `genpd_runtime_suspend()` of that device returns
  before trying. See `irq_safe_dev_in_sleep_domain()`.
  `genpd_sync_power_off()` makes no such test.
- `GENPD_FLAG_CPU_DOMAIN`: no power-off test in `drivers/pmdomain/core.c` reads
  it. `cpu_power_down_ok()` (runtime) and `cpu_system_power_down_ok()` (system
  suspend) of `pm_domain_cpu_gov` in `drivers/pmdomain/governor.c` apply their
  CPU checks only with the flag, and both can refuse the power-off.
- `GENPD_FLAG_MIN_RESIDENCY`: runtime only. `_default_power_down_ok()` compares
  state residency with the `next_wakeup` that devices set through
  `dev_pm_genpd_set_next_wakeup()`. The next hrtimer is read by
  `cpu_power_down_ok()`, under `GENPD_FLAG_CPU_DOMAIN`.
