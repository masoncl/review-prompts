- `set_hwmode_dev`: the one per-device callback called with the domain lock
  held, in `dev_pm_genpd_set_hwmode()`.
- `get_hwmode_dev`: called in `genpd_add_device()` before `genpd_lock()`.
- `attach_dev` and `get_hwmode_dev`: run under the global mutex `gpd_list_lock`,
  which every caller of `genpd_add_device()` holds. Calling `pm_genpd_init()` or
  `pm_genpd_add_subdomain()` from them deadlocks.
- `detach_dev`: no caller of `genpd_remove_device()` holds `gpd_list_lock`.
- `GENPD_FLAG_PM_CLK`: `pm_genpd_init()` assigns only `dev_ops.stop` and
  `dev_ops.start`, unconditionally. It does not touch `attach_dev` or
  `detach_dev`.
- Without `CONFIG_PM_CLK`: `pm_clk_suspend` and `pm_clk_resume` are defined as
  `NULL` in `include/linux/pm_clock.h`, so the flag clears both callbacks.
