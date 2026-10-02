- `genpd_remove()` returns `-EINVAL` only for a NULL or `ERR_PTR` argument.
  It does not test `gpd_list` membership; its next step is `genpd_lock()`
  through `lock_ops`.
- `has_provider` set: `-EBUSY`, tested before the other two conditions.
- Field names: there is no master_links; links are `parent_links` (this domain
  is the parent) and `child_links`. The device test is on `device_count`; the
  list itself is `dev_list`.
- `genpd->dev`: `of_genpd_del_provider()` does the `device_del()`;
  `genpd_remove()` only reaches `put_device()` in `genpd_free_data()`.
- `of_genpd_del_provider()` with no provider registered for `np`: changes
  nothing, so `has_provider` stays set.
- `genpd_remove()` frees the entries on the domain's own `child_links`, so a
  link to its parent never causes `-EBUSY`; only `parent_links` does.
- Unlinking before removal, in tree: `gdsc_unregister()` in
  `drivers/clk/qcom/gdsc.c` calls `of_genpd_del_provider()`, then
  `pm_genpd_remove_subdomain()` through `gdsc_pm_subdomain_remove()` for each
  domain that `gdsc_register()` linked to a parent, then `pm_genpd_remove()`.
- `of_genpd_remove_last()`: does not delete the provider and does not count
  domains. It runs `genpd_remove()` on the first `gpd_list` entry whose
  `provider` matches, which is the most recently initialised one.
- `of_genpd_remove_last()` stops at that first match even when removal fails,
  and returns the error as an `ERR_PTR`. In a loop, one busy domain ends the
  loop with the older domains still registered.
