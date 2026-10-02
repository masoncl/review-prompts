- Models do not know that `of_genpd_sync_state()` holds `gpd_list_lock` across
  `genpd_power_off()`, so `power_off` and the notifiers run under it there.
  `genpd_provider_sync_state()` with `GENPD_SYNC_STATE_SIMPLE` does not hold
  it.
- Models take detach to always succeed. `genpd_remove_device()` returns
  `-EAGAIN` while `prepared_count > 0`; `genpd_dev_pm_detach()` retries with
  doubling `mdelay()` below `GENPD_RETRY_MAX_MS`, then logs and returns with
  the device still attached and a virtual device not unregistered.
- Models do not know that single-domain attach sets up required OPPs itself:
  `__genpd_dev_pm_attach()` calls `genpd_set_required_opp_dev()` when
  `num_domains == 1`, which returns 0 at once when the consumer node has
  `#power-domain-cells`.
- Models do not know `pm_genpd_inc_rejected()` (a provider whose `power_off`
  returned 0 moves one count from `usage` to `rejected`; used in
  `drivers/cpuidle/cpuidle-psci.c`) or `dev_to_genpd_dev()` (used in
  `drivers/opp/core.c`).
