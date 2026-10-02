- `WQ_BH`: `__WQ_BH_ALLOWS` is `WQ_BH | WQ_HIGHPRI | WQ_PERCPU`; any other
  flag gives `WARN_ON_ONCE()` and NULL.
- `Documentation/core-api/workqueue.rst` says `WQ_HIGHPRI` is the only flag
  allowed with `WQ_BH`; the code also allows `WQ_PERCPU`.
- `WQ_MEM_RECLAIM` with `WQ_BH`: refused by the `__WQ_BH_ALLOWS` test;
  `init_rescuer()` has no test of `WQ_BH`.
- `WQ_SYSFS` with `__WQ_ORDERED`: accepted; `workqueue_sysfs_register()` has
  no test of `__WQ_ORDERED`. See "Ordered workqueues" for what sysfs can then
  change.
- `WQ_SYSFS` without `CONFIG_SYSFS`: accepted and does nothing;
  `workqueue_sysfs_register()` is a stub that returns 0.
- `__WQ_DEPRECATED`: a fifth internal flag, beside `__WQ_DESTROYING`,
  `__WQ_DRAINING`, `__WQ_ORDERED` and `__WQ_LEGACY`; only
  `workqueue_init_early()` sets it.
