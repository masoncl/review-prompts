- `dev` for a consumer with several domains: the virtual device, for example
  `pd_devs[i]`; the consumer's own `dev->pm_domain` is NULL.
- None of the helpers excludes a concurrent detach; `genpd_remove_device()`
  frees the `struct generic_pm_domain_data` that some of them read.

| Helper | Unattached `dev` | genpd lock | Requires of the caller |
|---|---|---|---|
| `dev_to_genpd_dev()` | `ERR_PTR(-EINVAL)` only if `dev->pm_domain` is NULL | no | `dev->pm_domain` must be a genpd, it is not tested; no `EXPORT_SYMBOL` |
| `dev_pm_genpd_set_performance_state()` | `-ENODEV` | yes | no provider callback needed; applied at once unless `pm_runtime_suspended()`, so also with runtime PM disabled |
| `dev_pm_genpd_add_notifier()` | `-ENODEV` | yes | one per device, else `-EEXIST`; callback runs under the genpd lock, except from `dev_pm_genpd_suspend()` and `dev_pm_genpd_resume()` on a domain without `GENPD_FLAG_IRQ_SAFE` |
| `dev_pm_genpd_remove_notifier()` | `-ENODEV` | yes | `-ENODEV` if none was added; `rpmh_rsc_pd_attach()` uses a devres action, which runs before the detach in `device_unbind_cleanup()` |
| `dev_pm_genpd_set_next_wakeup()` | no-op | no | no-op if the domain has no governor; read only for `GENPD_FLAG_MIN_RESIDENCY`, in `update_domain_next_wakeup()` |
| `dev_pm_genpd_get_next_hrtimer()` | `KTIME_MAX` | no | updated only by `cpu_power_down_ok()`; read it at `GENPD_NOTIFY_PRE_OFF`, as `rpmh_rsc_write_next_wakeup()` does |
| `dev_pm_genpd_synced_poweroff()` | no-op | yes | set after the domain is on: `_genpd_power_on()` clears it; only a provider that reads `synced_poweroff` acts, see `drivers/clk/qcom/gdsc.c` |
| `dev_pm_genpd_set_hwmode()` | `-ENODEV` | yes | `-EOPNOTSUPP` without `set_hwmode_dev`; power state is not checked |
| `dev_pm_genpd_get_hwmode()` | not checked, dereferences `dev->power.subsys_data` | no | caller must know `dev` is attached to a genpd |
| `dev_pm_genpd_rpm_always_on()` | `-ENODEV` | yes | does not power on; tested in `genpd_power_off()`, not in `genpd_sync_power_off()` |
| `dev_pm_genpd_is_on()` | `false` | yes | result is a snapshot |
| `dev_pm_genpd_suspend()`, `dev_pm_genpd_resume()` | no-op | only with `GENPD_FLAG_IRQ_SAFE` | caller excludes all other genpd activity otherwise; calls must pair, they count in `suspended_count`; stubs without `CONFIG_PM_GENERIC_DOMAINS_SLEEP` |

- **Unsafe usage**: calling a helper marked "yes" under genpd lock from a
  power notifier callback of the same domain.
  - Unsafe: every caller of `genpd_power_on()` and `genpd_power_off()` holds
    the genpd lock around the notifier chain, so the helper deadlocks.
  - Safe: `dev_pm_genpd_get_next_hrtimer()`, which takes no lock, as
    `rpmh_rsc_pd_callback()` reaches it through `rpmh_flush()`.
  - Safe: a callback that only signals, as `cxpd_notifier_cb()` does.
