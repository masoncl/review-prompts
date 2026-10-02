- `platform_probe()`: passes
  `PD_FLAG_ATTACH_POWER_ON | PD_FLAG_DETACH_POWER_OFF`; no caller of
  `dev_pm_domain_attach()` passes `PD_FLAG_DEV_LINK_ON`.
- Buses that pass other flags: `sdio_bus_probe()` and `sdw_bus_probe()` pass
  0; `dp_aux_ep_probe()` passes only `PD_FLAG_ATTACH_POWER_ON`;
  `i2c_device_probe()` drops `PD_FLAG_ATTACH_POWER_ON` when
  `i2c_acpi_waive_d0_probe()` is true.
- Detach: `platform_probe()` and the platform bus do not detach;
  `device_unbind_cleanup()` in `drivers/base/dd.c` does, after
  `devres_release_all()`, on probe failure and on unbind.
- Buses with their own detach: `dp_aux_ep_probe()` on error and
  `dp_aux_ep_remove()` call `dev_pm_domain_detach()` themselves.
- `amba_read_periphid()`: called from `amba_device_add()` and
  `amba_match()`, attaches with `PD_FLAG_ATTACH_POWER_ON` and detaches again
  before any probe; `amba_probe()` attaches a second time.
- `prevent_deferred_probe` in `platform_probe()`: also covers the attach, so
  `-EPROBE_DEFER` from `dev_pm_domain_attach()` becomes `-ENXIO`.
