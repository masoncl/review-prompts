- **Potentially unsafe usage**: passing `is_off` true without reading or
  forcing the hardware state.
  - Unsafe: when the hardware may be on; genpd records it off, the parent's
    `sd_count` is not raised in `genpd_add_subdomain()`, and the first use
    runs `->power_on()` on live hardware.
  - Safe: after forcing the hardware off and reading the status back, as
    `exynos_pd_probe()` does for "samsung,exynos4210-pd" on `CONFIG_ARM`.
  - Safe: likewise `rockchip_pm_add_one_domain()`, which powers off
    `need_regulator` domains first and then passes the status it reads.
  - Safe: when the state is the kernel's vote to firmware and the driver
    holds the boot level itself until its sync_state, as
    `rpmhpd_aggregate_corner()` does while `state_synced` is false.
- **Potentially unsafe usage**: passing `is_off` false as a constant.
  - Unsafe: when the hardware may be off; `genpd_power_on()` returns 0
    early for a domain recorded on, so `->power_on()` does not run until
    genpd has powered the domain off.
  - Safe: after powering the hardware on and checking the result, as
    `scpsys_add_one_domain()` in
    `drivers/pmdomain/mediatek/mtk-pm-domains.c` does for a domain without
    `MTK_SCPD_KEEP_DEFAULT_OFF`.
- `th1520_pd_probe()`: calls `pm_genpd_init()` with true first, then
  `th1520_pd_init_all_off()`, before `of_genpd_add_provider_onecell()`; a
  failed power-off is only logged.
- `drivers/pmdomain/ti/ti_sci_pm_domains.c`: passes `!is_on` from
  `ti_sci_pm_pd_is_on()`, not a constant.
- `is_off` false: the first power callback genpd makes is `->power_off()`,
  so the driver must already hold what that releases; `imx93_pd_probe()`
  enables the clocks when it finds the domain on.
- `GENPD_FLAG_ALWAYS_ON` or `GENPD_FLAG_RPM_ALWAYS_ON` with `is_off` true:
  `pm_genpd_init()` returns `-EINVAL`; `apple_pmgr_ps_probe()` powers the
  domain on first for that reason.
