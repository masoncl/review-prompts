- `struct dev_pm_domain`: one per domain, not per device. It is the `domain`
  field of `struct generic_pm_domain`; every member's `dev->pm_domain` points
  at the same one.
- `domain.ops`: filled in by `pm_genpd_init()`. Attach only points
  `dev->pm_domain` at `domain`, in `genpd_add_device()`.
- `domain.detach` and `domain.sync`: written only by
  `__genpd_dev_pm_attach()`. `pm_genpd_add_device()` and
  `of_genpd_add_device()` do not set them.
- Runtime PM callbacks: `__genpd_runtime_suspend()` takes the first of type,
  class and bus that has a `pm`, and falls back to driver ops when that one
  has no callback.
- System sleep callbacks: `pm_genpd_init()` sets only `prepare`, the six noirq
  ops and `complete`. Its noirq ops call driver ops directly (`CALL_PM_OP()`
  in `drivers/base/power/generic_ops.c`). For the other phases
  `drivers/base/power/main.c` goes from the NULL domain op straight to driver
  ops. Type, class and bus sleep ops do not run for a genpd member.
- Active devices: genpd keeps no counter of them. `genpd_power_off()` walks
  `dev_list` and asks `pm_runtime_suspended()` for each device.
- `sd_count`: counts children that are on, not devices.
- `prepared_count`: written only in `genpd_prepare()` and `genpd_complete()`.
- `suspended_count`: written only in `genpd_finish_suspend()`,
  `genpd_finish_resume()` and `genpd_switch_state()`, not by the runtime PM
  callbacks.
- `parent_links`: the links in which this domain is the parent, so it lists
  its children. `child_links` lists its parents. Walks toward the root use
  `child_links`.
- `pm_domain_cpu_gov`: defined only under `CONFIG_CPU_IDLE`.
- Device's performance vote: `genpd_runtime_suspend()` sets it to 0 and parks
  the old value in `rpm_pstate`; `genpd_runtime_resume()` restores it. Both
  skip this for an IRQ-safe device in a domain without `GENPD_FLAG_IRQ_SAFE`.
- OPP core entry point: `_set_opp_level()` in `drivers/opp/core.c` calls
  `dev_pm_domain_set_performance_state()`, not
  `dev_pm_genpd_set_performance_state()`. Both end in
  `genpd_dev_pm_set_performance_state()`.
- Device links to virtual devices: of the attach functions in
  `drivers/base/power/common.c`, only `dev_pm_domain_attach_list()` and its
  devres wrapper `devm_pm_domain_attach_list()` create them, and not with
  `PD_FLAG_NO_DEV_LINK`. After `dev_pm_domain_attach_by_id()` or
  `dev_pm_domain_attach_by_name()` the caller has a bare virtual device with
  runtime PM enabled and no link.
- `struct of_genpd_provider` and its domains: a domain has no pointer to its
  provider, and the provider reaches domains only through the opaque `data`
  that it passes to `xlate`.
  A domain belongs to a provider when `genpd->provider` equals the provider
  node's fwnode. `of_genpd_del_provider()`, `of_genpd_remove_last()` and
  `of_genpd_sync_state()` find domains by scanning `gpd_list` for that match.
- `has_provider`: `genpd_remove()` returns `-EBUSY` while it is set, before
  it looks at devices or children. `of_genpd_del_provider()` clears it.
- The domain's own `dev`: `pm_genpd_init()` only initializes it.
  `device_add()` happens in `of_genpd_add_provider_simple()` and
  `of_genpd_add_provider_onecell()`, on `genpd_provider_bus_type`.
- `genpd_bus_type` and `genpd_provider_bus_type`: two buses. The first holds
  the virtual consumer devices, the second the domains' own devices.
