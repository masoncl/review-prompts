- Callback layer choice: the core picks the layer by which ops table exists,
  in the order `dev->pm_domain`, `dev->type->pm`, `dev->class->pm`,
  `dev->bus->pm`; a layer whose table lacks the callback for this phase still
  wins over the layers below it.
- Device attached to a genpd: `pm_genpd_init()` in `drivers/pmdomain/core.c`
  sets only `prepare`, the noirq callbacks, `complete`, `runtime_suspend` and
  `runtime_resume`, so in the suspend/resume and late/early phases the lookup
  goes to the driver callback with the bus, class and type tables bypassed,
  unless the provider filled in another member itself, as
  `drivers/pmdomain/ti/ti_sci_pm_domains.c` does for `suspend`.
- `dpm_list` membership: `device_pm_add()` returns before adding a device
  with `power.no_pm` set (`device_set_pm_not_required()`).
- `dpm_list` order: registration order, then changed by
  `device_reorder_to_tail()` in `drivers/base/core.c`, which
  `device_link_add()` runs on the consumer, its children and its consumers;
  links with `DL_FLAG_SYNC_STATE_ONLY` do not reorder.
- `struct syscore`: what `register_syscore()` takes; it carries a
  `struct syscore_ops` pointer and a `data` pointer passed to every callback.
  There is no register_syscore_ops() here.
- Suspend-to-idle: uses `struct platform_s2idle_ops`, which has no `enter`
  member; `suspend_enter()` in `kernel/power/suspend.c` goes to
  `s2idle_loop()` and skips CPU offlining, `syscore_suspend()` and
  `suspend_ops->enter()`.
- `dev->power.wakeup`, with `CONFIG_PM_SLEEP`: non-NULL only while wakeup is
  enabled; `device_wakeup_enable()` creates the `struct wakeup_source`,
  `device_wakeup_disable()` destroys it. `power.can_wakeup` is capability
  only.
- `ws->dev` in `struct wakeup_source`: a separate child device made by
  `wakeup_source_sysfs_add()` for statistics, not the device that owns the
  source.
- `struct wake_irq`: also created by `dev_pm_set_wake_irq()` for the ordinary
  device interrupt, not only for a dedicated one. Runtime PM enables and
  disables only dedicated ones (`WAKE_IRQ_DEDICATED_MASK`).
- `struct wake_irq` and system sleep: armed through `ws->wakeirq` by
  `device_wakeup_arm_wake_irqs()`, so only when the device has a wakeup
  source attached and `device_may_wakeup()` is true.
- `struct dev_pm_qos`: also embeds `struct freq_constraints` for
  `DEV_PM_QOS_MIN_FREQUENCY` and `DEV_PM_QOS_MAX_FREQUENCY`.
- `dev->power.qos`: three states, NULL (never allocated), valid, and
  `ERR_PTR(-ENODEV)` after `dev_pm_qos_constraints_destroy()` freed an
  allocated one; a NULL test alone does not cover the last.
- Global CPU QoS: two constraint sets in `kernel/power/qos.c`,
  `cpu_latency_constraints` under `CONFIG_CPU_IDLE` and
  `cpu_wakeup_latency_constraints` under
  `CONFIG_PM_QOS_CPU_SYSTEM_WAKEUP`; `cpu_wakeup_latency_qos_limit()` is read
  by, for example, `drivers/pmdomain/governor.c`.
- Device in several power domains: `dev->pm_domain` holds one domain only.
  `genpd_dev_pm_attach_by_id()` creates one virtual device per domain on
  `genpd_bus_type`; `dev_pm_domain_attach_list()` in
  `drivers/base/power/common.c` links each to the real device with a
  `struct device_link` unless `PD_FLAG_NO_DEV_LINK` is set.
- `struct generic_pm_domain`: is itself a device; it embeds a `struct device`
  on `genpd_provider_bus_type`, distinct from the virtual devices above.
- `RPM_BLOCKED`: a value of `enum rpm_status` kept in `power.last_status`, not
  `power.runtime_status`. `device_prepare()` sets it through
  `pm_runtime_block_if_disabled()` on a device whose runtime PM is disabled and
  was never enabled; `pm_runtime_enable()` warns while it is set;
  `device_complete()` clears it with `pm_runtime_unblock()`.
