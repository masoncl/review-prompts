- Boot pause: `defer_sync_state_count` in `drivers/base/core.c` starts at
  1; `sync_state_resume_initcall()` drops it at late_initcall.
- `drivers/of/platform.c` holds a second pause from
  `of_platform_default_populate_init()` until
  `of_platform_sync_state_init()` at late_initcall_sync.
- `fw_devlink=permissive`: links are still created, with
  `DL_FLAG_SYNC_STATE_ONLY`; they are managed, so sync_state still waits
  for consumers.
- `fw_devlink=off`: `fw_devlink_link_device()` returns before it parses or
  creates any link; with no managed consumer link, sync_state runs once the
  provider is bound and the pause is lifted.
- `fw_devlink_probing_done()`: forces sync_state on suppliers still waiting
  only in timeout mode, set by `fw_devlink.sync_state=timeout` or
  `CONFIG_FW_DEVLINK_SYNC_STATE_TIMEOUT`; in strict mode, the default,
  `fw_devlink_dev_sync_state()` only logs and the domains keep `stay_on`.
  It has two call sites in `drivers/base/dd.c`.
- Without `CONFIG_MODULES`: `CONFIG_DRIVER_DEFERRED_PROBE_TIMEOUT` defaults
  to 0 and `deferred_probe_initcall()` calls `fw_devlink_probing_done()`
  once, at late_initcall.
- With `CONFIG_MODULES`: only `deferred_probe_timeout_work_func()` calls
  it; the work is scheduled only if `driver_deferred_probe_timeout` is
  above 0.
- `fw_devlink_dev_sync_state()`: skips a supplier whose `links.defer_sync`
  is not empty, that is, one still parked by the boot pause.
- `state_synced` sysfs attribute of the supplier: writing "1" calls its
  sync_state at once; see `state_synced_store()` in `drivers/base/dd.c`.
- Granularity is the supplier device: with a provider device or onecell,
  one missing consumer holds every domain of the node; with a no-device
  simple provider, only that one domain.
