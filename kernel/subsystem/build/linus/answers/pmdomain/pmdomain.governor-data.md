- Default power state: `genpd_alloc_data()` sets it up when `state_count == 0`,
  with or without a governor.
- `struct genpd_governor_data`: there is no last_enable field; the field is
  `last_enter`.
- Device latency: measured in `genpd_runtime_suspend()` and
  `genpd_runtime_resume()` only when `td` is set and `pm_runtime_enabled(dev)`.
- Provider latency: `_genpd_power_off()` and `_genpd_power_on()` time the
  callback only when `timed` is true, `genpd->gd` is set and the state's
  `fwnode` is NULL.
- `genpd_sync_power_off()` and `genpd_sync_power_on()`: pass `timed` false, so
  they never update the provider latencies.
- `genpd_reflect_residency()` (`CONFIG_DEBUG_FS`): updates the `above` and
  `below` counters only when `genpd->gd` is set and `reflect_residency` is
  true; only `cpu_power_down_ok()` sets that.
- **Potentially unsafe usage**: dereferencing `genpd->gd` or `gpd_data->td`
  with no NULL test.
  - Unsafe: in code that runs for a domain registered with a NULL governor;
    `genpd_alloc_data()` and `genpd_alloc_dev_data()` leave both NULL.
  - Unsafe: for another domain's `gd`, since a parent or subdomain may have no
    governor.
  - Safe: in a governor callback, for the domain's own data, as
    `default_suspend_ok()` does; the callback runs only when `genpd->gov` is
    set.
  - Safe: `genpd->gd` inside a test of `td`, as `genpd_runtime_suspend()` does;
    `genpd_add_device()` allocates `td` only when `genpd->gd` is set.
  - Safe: after a test of the other domain's pointer, as
    `__default_power_down_ok()` does with `link->child->gd`.
