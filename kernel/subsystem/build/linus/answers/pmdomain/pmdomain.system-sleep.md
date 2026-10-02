- `genpd_sync_power_off()` count test: returns unless
  `suspended_count == device_count`; `prepared_count` is not compared.
- `genpd_sync_power_off()` also leaves the domain on for:
  `GENPD_FLAG_ALWAYS_ON`, `sd_count > 0`, a subdomain not in its deepest
  state, a false `system_power_down_ok`, a non-zero `_genpd_power_off()`.
- Not tested by `genpd_sync_power_off()`: `GENPD_FLAG_RPM_ALWAYS_ON`, the
  per-device `rpm_always_on`, `GENPD_FLAG_NO_SYNC_STATE`.
- Wake-path test in `genpd_finish_suspend()`: `device_awake_path(dev) &&
  genpd_is_active_wakeup(genpd) && !device_out_band_wakeup(dev)`; it does not
  call `device_may_wakeup()`.
- Device with `device_out_band_wakeup()` true: is stopped and counted like any
  other, so `GENPD_FLAG_ACTIVE_WAKEUP` does not keep the domain on for it.
- `genpd_finish_resume()`: makes the same three-part test and then skips
  `genpd_sync_power_on()` and `suspended_count--`.
- `genpd_prepare()` on a positive `pm_generic_prepare()`: returns 0;
  `prepared_count` stays incremented, `genpd_prepare()` undoes it only for a
  negative value.
- `dev_pm_genpd_suspend()` and `dev_pm_genpd_resume()`: reach
  `genpd_sync_power_off()` and `genpd_sync_power_on()` outside the noirq
  phase, for example for syscore and suspend-to-idle users.
