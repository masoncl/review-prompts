- `PD_FLAG_ATTACH_POWER_ON` and `PD_FLAG_DETACH_POWER_OFF`: not read by
  `dev_pm_domain_attach_list()`; setting them in `pd_flags` changes nothing.
- `PD_FLAG_DEV_LINK_ON`: the only flag that powers the domain on at attach;
  no effect together with `PD_FLAG_NO_DEV_LINK`.
- `PD_FLAG_DEV_LINK_ON` power-on does not last: `__rpm_put_suppliers()` drops
  the link's reference when the consumer runtime-suspends or is set
  `RPM_SUSPENDED`; after that the domain follows the consumer.
- `PD_FLAG_NO_DEV_LINK`: exists under that name in
  `include/linux/pm_domain.h`; `pd_links[i]` stays NULL.
- `PD_FLAG_REQUIRED_OPP`: calls `dev_pm_opp_set_config()` with the virtual
  device as `required_dev` and the loop index as `required_dev_index`; no
  power change.
- With no flags each attach still applies the `required-opps` level for that
  index as the virtual device's default performance state; see
  `genpd_set_required_opp()`, called from `__genpd_dev_pm_attach()`.
