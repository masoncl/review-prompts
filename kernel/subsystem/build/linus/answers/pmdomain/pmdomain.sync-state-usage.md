- **Unsafe usage**: a provider driver's own sync_state callback that
  returns without calling `of_genpd_sync_state()` for a node whose domains
  were registered on without `GENPD_FLAG_NO_STAY_ON`.
  - Unsafe: when the node has a device bound to that driver, or the domains
    set `GENPD_FLAG_NO_SYNC_STATE`: `dev_set_drv_sync_state()` returns
    `-EBUSY` for a driver with its own callback, the core ignores the
    result, nothing else clears `stay_on`, and `genpd_power_off()` keeps
    returning early.
  - Safe: provider node is the device's own node; call it with
    `dev->of_node`, as `rpmhpd_sync_state()` and `rpmpd_sync_state()` do.
  - Safe: provider nodes are child nodes; call it once per child, as
    `tegra_pmc_sync_state()` in `drivers/soc/tegra/pmc.c` does when the
    device node has a "powergates" child.
  - Safe: a child device registered the provider on the parent's node; the
    parent's callback calls it, as `zynqmp_firmware_sync_state()` does for
    `zynqmp_gpd_probe()` on a "xlnx,zynqmp-firmware" node.
- Node match: `of_genpd_sync_state()` compares `genpd->provider` with the
  fwnode of the node given to the registration function; another node
  matches nothing and fails silently.
- `of_genpd_sync_state()`: clears `stay_on` and calls `genpd_power_off()`
  for every matching domain, whatever its flags; it is an empty stub
  without `CONFIG_PM_GENERIC_DOMAINS_OF`.
- Child-node providers under a parent driver's callback: set
  `GENPD_FLAG_NO_SYNC_STATE`, as `tegra_pmc_core_pd_add()` does; without
  it `genpd->dev` takes the child fwnode and releases the domain itself.
- `GENPD_FLAG_NO_SYNC_STATE`: set only in `drivers/soc/tegra/pmc.c`.
- `drivers/cpuidle/` and `drivers/pmdomain/imx/gpcv2.c`: have no sync_state
  callback.
- `rpmhpd_probe()`, `rpmpd_probe()` and `zynqmp_gpd_probe()` pass `is_off`
  true for every domain, so `stay_on` is never set there; of the four
  drivers above, only `tegra_pmc_core_pd_add()` registers a domain on.
