- `genpd_sync_state()`: the callback the core installs on the provider's
  driver with `dev_set_drv_sync_state()`, only when that driver has no
  `sync_state` of its own.
- `genpd_provider_sync_state()`: the callback of `genpd_provider_drv`, which
  binds every `genpd->dev` that provider registration adds; it is never
  installed on a provider's driver.
- Device lookup: `get_dev_from_fwnode()` on the node's fwnode, before
  `genpd_add_provider()` is called.
- No device for the node and `GENPD_FLAG_NO_SYNC_STATE` clear: `genpd->dev`
  takes the fwnode with `device_set_node()` and becomes the supplier device;
  there is no later scan.
- Device exists but `dev->driver` is NULL at registration:
  `dev_set_drv_sync_state()` returns 0 and installs nothing, and no
  `genpd->dev` takes the fwnode; the core has then installed nothing that
  clears `stay_on`.
- `GENPD_FLAG_NO_SYNC_STATE`: tested only on the no-device path; when a
  device exists, `dev_set_drv_sync_state()` is called whatever the flag.

| | `of_genpd_add_provider_simple()` | `of_genpd_add_provider_onecell()` |
|---|---|---|
| no device, flag clear | this domain: `GENPD_SYNC_STATE_SIMPLE` | first such domain in the array: `GENPD_SYNC_STATE_ONECELL` |
| callback releases | only that domain | every domain of the node, via `of_genpd_sync_state()` |
| other domains | none | stay `GENPD_SYNC_STATE_OFF`, no fwnode |

- `GENPD_SYNC_STATE_OFF` domains: `genpd->dev` is still added and bound;
  `genpd_provider_sync_state()` does nothing for them.
