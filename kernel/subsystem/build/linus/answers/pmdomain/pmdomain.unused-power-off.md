- `GENPD_FLAG_RPM_ALWAYS_ON`: `genpd_power_off()` returns for it
  unconditionally, with or without an active device.
- `pd_ignore_unused`: read only in `genpd_power_off_unused()`;
  `of_genpd_sync_state()` and runtime PM still power domains off with the
  option given.
- `GENPD_FLAG_NO_STAY_ON` in `rockchip_pm_add_one_domain()`: the tree gives
  no reason for it; nothing in the tree ties it to the regulator cleanup.
- There is no pm_domain_always_on command line option; the only option in
  `drivers/pmdomain/` is `pd_ignore_unused`.
