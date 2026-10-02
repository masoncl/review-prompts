- Enforced order: only `pm_genpd_init()` first. Provider registration tests
  `genpd_present()`; link-before-register is not checked anywhere.
- `pm_genpd_add_subdomain()`: has no `genpd_present()` test and locks both
  domains through `lock_ops`, which `pm_genpd_init()` sets.
- Linking after registration: `genpd_add_subdomain()` returns `-EINVAL` when
  the parent is off and the subdomain is on; `__genpd_dev_pm_attach()` can
  power the subdomain on once the provider is visible.
- `of_genpd_add_child_ids()`: a third way to link. It takes children from
  `data->domains` and parents from `genpd_get_from_provider()`, so the parent's
  provider must be registered; `scmi_pm_domain_probe()` calls it after
  `of_genpd_add_provider_onecell()`.
- Per-domain check: there is no pm_genpd_present() here; it is static
  `genpd_present()` in `drivers/pmdomain/core.c`, which takes `gpd_list_lock`
  itself. Onecell does not hold that lock across its loop.
- Empty slot: `of_genpd_add_provider_onecell()` skips a NULL entry of
  `data->domains`, in the registration loop and in the unwind.
- `genpd_set_default_power_state()`: not called by onecell; `genpd_alloc_data()`
  calls it from `pm_genpd_init()` when `state_count` is 0.
- After any failed `of_genpd_add_provider_onecell()`: no domain in the array
  has `has_provider` set and each added `genpd->dev` has had `device_del()`, so
  `pm_genpd_remove()` needs no `of_genpd_del_provider()` first.
