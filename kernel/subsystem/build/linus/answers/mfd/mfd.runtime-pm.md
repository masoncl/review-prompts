- Step: when the cell sets `pm_runtime_no_callbacks`, `mfd_add_device()`
  calls `pm_runtime_no_callbacks()` after `platform_device_add()` has
  returned 0, as its last action on the device.
- Child probe: can run inside `platform_device_add()`, so the child driver's
  probe may see `power.no_callbacks` still 0.
- Sysfs: the device is already registered, so `dpm_sysfs_add()` has created
  the runtime attributes and `rpm_sysfs_remove()` then removes them.
- `rpm_sysfs_remove()`: unmerges all of `pm_runtime_attr_group`, which
  includes `control`; see `runtime_attrs` in `drivers/base/power/sysfs.c`.
- Enabling: `mfd_add_device()` makes no other runtime PM call; the child
  stays disabled until its driver calls `pm_runtime_enable()`.
- Flag on a disabled child: no effect on transitions; `rpm_resume()` and
  `rpm_check_suspend_allowed()` return on `power.disable_depth` before any
  test of `power.no_callbacks`.
- `rpm_resume()` of a flagged child: skips the parent only when the parent is
  `RPM_ACTIVE`, disabled, or has `power.ignore_children`; otherwise it resumes
  the parent first and returns `-EBUSY` if the parent does not become active.
- `power.child_count` of the parent: follows the child's `runtime_status`,
  not whether the child's runtime PM is enabled.
- `pm_runtime_set_active()` on a disabled child: on success increments the
  parent's `child_count`, so the child blocks parent suspend unless the
  parent has `power.ignore_children`; see `__pm_runtime_set_status()` in
  `drivers/base/power/runtime.c`.
- `pm_runtime_disable()` on an active child: leaves `child_count` unchanged,
  so the parent stays blocked until the child's status becomes
  `RPM_SUSPENDED`.
- **Potentially unsafe usage**: `pm_runtime_set_active()` in a child's probe.
  - Unsafe: when the parent has runtime PM enabled, is not `RPM_ACTIVE` and
    has not set `power.ignore_children`, which during probe means the
    parent's runtime resume failed; `__pm_runtime_set_status()` returns
    `-EBUSY` and leaves the child `RPM_SUSPENDED`.
  - Safe: when the parent has runtime PM enabled and its runtime resume
    succeeds; `__driver_probe_device()` in `drivers/base/dd.c` calls
    `pm_runtime_get_sync()` on the parent before the probe and
    `pm_runtime_put()` after it, so the parent is `RPM_ACTIVE` for the test
    in `__pm_runtime_set_status()`.
  - Safe: when the parent is `RPM_ACTIVE` or has runtime PM disabled at that
    point, which is what `__pm_runtime_set_status()` tests; for example
    `dln2_spi_probe()` in `drivers/spi/spi-dln2.c`, whose parent never
    enables runtime PM because `dln2_driver` does not set
    `supports_autosuspend`.
