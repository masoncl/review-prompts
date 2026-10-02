| Flag | Read by | Effect |
|---|---|---|
| `PD_FLAG_ATTACH_POWER_ON` | `dev_pm_domain_attach()`, passed as `power_on` to `acpi_dev_pm_attach()` only | ACPI: device put in D0. DT: not passed on |
| `PD_FLAG_DETACH_POWER_OFF` | `dev_pm_domain_attach()` | saved in `dev->power.detach_power_off`, only if `dev->pm_domain` is set after the attach |

- `dev_pm_domain_attach()`: reads no other flag; `PD_FLAG_NO_DEV_LINK`,
  `PD_FLAG_DEV_LINK_ON` and `PD_FLAG_REQUIRED_OPP` are read only by
  `dev_pm_domain_attach_list()`.
- `genpd_dev_pm_attach()`: takes no flags and always powers the domain on,
  also for callers that pass 0, such as `sdio_bus_probe()`.
- `dev->power.detach_power_off`: passed to `dev_pm_domain_detach()` by
  `device_unbind_cleanup()`; `acpi_dev_pm_detach()` acts on it,
  `genpd_dev_pm_detach()` ignores its `power_off` argument.
- `genpd_dev_pm_attach()` returns 0 when the number of `power-domains`
  entries is not exactly 1.
- Provider not registered: there is no of_genpd_get_from_provider() here;
  `genpd_get_from_provider()` fails and `__genpd_dev_pm_attach()` returns
  `driver_deferred_probe_check_state()`.
- `driver_deferred_probe_check_state()` once `initcalls_done` is set:
  `-ENODEV` without `CONFIG_MODULES`, `-ETIMEDOUT` when
  `driver_deferred_probe_timeout` is 0; `-EPROBE_DEFER` in every other case.
- `__genpd_dev_pm_attach()`: sets only `->detach` and `->sync` of the
  `struct dev_pm_domain`; `->start` and `->set_performance_state` are set
  in `pm_genpd_init()`.
