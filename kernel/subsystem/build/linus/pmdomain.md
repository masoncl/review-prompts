# Power Domain Subsystem

## Main structures

### Objects and how they relate

- `struct dev_pm_domain`: one per domain, not per device. It is the `domain`
  field of `struct generic_pm_domain`; every member's `dev->pm_domain` points
  at the same one.
- `domain.ops`: filled in by `pm_genpd_init()`. Attach only points
  `dev->pm_domain` at `domain`, in `genpd_add_device()`.
- `domain.detach` and `domain.sync`: written only by
  `__genpd_dev_pm_attach()`. `pm_genpd_add_device()` and
  `of_genpd_add_device()` do not set them.
- Runtime PM callbacks: `__genpd_runtime_suspend()` takes the first of type,
  class and bus that has a `pm`, and falls back to driver ops when that one
  has no callback.
- System sleep callbacks: `pm_genpd_init()` sets only `prepare`, the six noirq
  ops and `complete`. Its noirq ops call driver ops directly (`CALL_PM_OP()`
  in `drivers/base/power/generic_ops.c`). For the other phases
  `drivers/base/power/main.c` goes from the NULL domain op straight to driver
  ops. Type, class and bus sleep ops do not run for a genpd member.
- Active devices: genpd keeps no counter of them. `genpd_power_off()` walks
  `dev_list` and asks `pm_runtime_suspended()` for each device.
- `sd_count`: counts children that are on, not devices.
- `prepared_count`: written only in `genpd_prepare()` and `genpd_complete()`.
- `suspended_count`: written only in `genpd_finish_suspend()`,
  `genpd_finish_resume()` and `genpd_switch_state()`, not by the runtime PM
  callbacks.
- `parent_links`: the links in which this domain is the parent, so it lists
  its children. `child_links` lists its parents. Walks toward the root use
  `child_links`.
- `pm_domain_cpu_gov`: defined only under `CONFIG_CPU_IDLE`.
- Device's performance vote: `genpd_runtime_suspend()` sets it to 0 and parks
  the old value in `rpm_pstate`; `genpd_runtime_resume()` restores it. Both
  skip this for an IRQ-safe device in a domain without `GENPD_FLAG_IRQ_SAFE`.
- OPP core entry point: `_set_opp_level()` in `drivers/opp/core.c` calls
  `dev_pm_domain_set_performance_state()`, not
  `dev_pm_genpd_set_performance_state()`. Both end in
  `genpd_dev_pm_set_performance_state()`.
- Device links to virtual devices: of the attach functions in
  `drivers/base/power/common.c`, only `dev_pm_domain_attach_list()` and its
  devres wrapper `devm_pm_domain_attach_list()` create them, and not with
  `PD_FLAG_NO_DEV_LINK`. After `dev_pm_domain_attach_by_id()` or
  `dev_pm_domain_attach_by_name()` the caller has a bare virtual device with
  runtime PM enabled and no link.
- `struct of_genpd_provider` and its domains: a domain has no pointer to its
  provider, and the provider reaches domains only through the opaque `data`
  that it passes to `xlate`.
  A domain belongs to a provider when `genpd->provider` equals the provider
  node's fwnode. `of_genpd_del_provider()`, `of_genpd_remove_last()` and
  `of_genpd_sync_state()` find domains by scanning `gpd_list` for that match.
- `has_provider`: `genpd_remove()` returns `-EBUSY` while it is set, before
  it looks at devices or children. `of_genpd_del_provider()` clears it.
- The domain's own `dev`: `pm_genpd_init()` only initializes it.
  `device_add()` happens in `of_genpd_add_provider_simple()` and
  `of_genpd_add_provider_onecell()`, on `genpd_provider_bus_type`.
- `genpd_bus_type` and `genpd_provider_bus_type`: two buses. The first holds
  the virtual consumer devices, the second the domains' own devices.

## Where to look

**Core files**

| Job | File | Easy to miss |
|---|---|---|
| `struct dev_pm_domain` | `include/linux/pm.h` | not in `include/linux/pm_domain.h` |
| DT bindings, generic | `Documentation/devicetree/bindings/power/power-domain.yaml`, `Documentation/devicetree/bindings/power/domain-idle-state.yaml` and `Documentation/devicetree/bindings/power/power_domain.txt` | `power-domain.yaml` is the provider schema; of the three, only `power_domain.txt` describes `power-domain-names` |
| DT bindings, per provider | search `Documentation/devicetree/bindings/` for `#power-domain-cells` | also in other subdirectories, for example `clock/`, `soc/`, `firmware/` and `arm/` |
| cpuidle: shared CPU-domain helpers | `drivers/cpuidle/dt_idle_genpd.c` | built under `CONFIG_DT_IDLE_GENPD` |
| cpuidle: PSCI domains | `drivers/cpuidle/cpuidle-psci-domain.c` | CPUs are attached from `drivers/cpuidle/cpuidle-psci.c` via `dt_idle_attach_cpu()` |
| cpuidle: RISC-V SBI domains | `drivers/cpuidle/cpuidle-riscv-sbi.c` | domains and CPU attach in the one file; see `sbi_pd_init()` |
| Providers inside | directories listed in `drivers/pmdomain/Makefile` | `arm/` holds SCMI and SCPI; `ti/` holds `omap_prm.c` and `ti_sci_pm_domains.c` |
| Providers outside, largest group | `drivers/clk/` | `drivers/clk/qcom/gdsc.c` serves every Qualcomm clock controller that sets `.gdscs` |
| Providers outside, rest | search for `pm_genpd_init(` outside `drivers/pmdomain/` | see below |

- `Documentation/devicetree/bindings/power/` subdirectories: not per-vendor;
  `supply/` and `reset/` hold power-supply and reset bindings, and
  `avs/qcom,cpr.yaml` is the only genpd provider binding in a subdirectory.
- `drivers/firmware/`: no file there calls `pm_genpd_init()`; the SCMI, SCPI,
  TI SCI, i.MX SCU and ZynqMP providers are all under `drivers/pmdomain/`.
- `drivers/soc/`: the only providers there are `drivers/soc/tegra/pmc.c`
  and `drivers/soc/dove/pmu.c`.
- `arch/`: the only caller of `pm_genpd_init()` is
  `arch/arm/mach-s3c/pm-s3c64xx.c`.
- Unexpected providers: `drivers/irqchip/irq-qcom-mpm.c`,
  `drivers/gpu/drm/amd/amdgpu/amdgpu_acp.c` and
  `drivers/gpu/drm/amd/amdgpu/isp_v4_1_1.c`.
- No OF provider: the two amdgpu files and
  `arch/arm/mach-s3c/pm-s3c64xx.c` call neither
  `of_genpd_add_provider_simple()` nor `of_genpd_add_provider_onecell()`;
  they add devices with `pm_genpd_add_device()`,
  `arch/arm/mach-s3c/pm-s3c64xx.c` only under `CONFIG_S3C_DEV_FB`.

## Domains

**Domain flags**

- `GENPD_FLAG_RPM_ALWAYS_ON`: the one flag the core sets. `pm_genpd_init()` ORs
  it in when `gov` is `&pm_domain_always_on_gov`, before the always-on check, so
  that governor with `is_off` true returns `-EINVAL`.
- `GENPD_FLAG_NO_SYNC_STATE`: tested only when the provider node has no
  `struct device`, in `of_genpd_add_provider_simple()` and
  `of_genpd_add_provider_onecell()`. `genpd->sync_state` then stays
  `GENPD_SYNC_STATE_OFF` and, unless another domain of the same onecell node
  carries the callback, the provider has to call `of_genpd_sync_state()`
  itself to clear `stay_on`, as `drivers/soc/tegra/pmc.c` does.
- `GENPD_FLAG_IRQ_SAFE` changes runtime power-off: without it, each attached
  device with `pm_runtime_is_irq_safe()` is counted as not suspended in
  `genpd_power_off()`, and `genpd_runtime_suspend()` of that device returns
  before trying. See `irq_safe_dev_in_sleep_domain()`.
  `genpd_sync_power_off()` makes no such test.
- `GENPD_FLAG_CPU_DOMAIN`: no power-off test in `drivers/pmdomain/core.c` reads
  it. `cpu_power_down_ok()` (runtime) and `cpu_system_power_down_ok()` (system
  suspend) of `pm_domain_cpu_gov` in `drivers/pmdomain/governor.c` apply their
  CPU checks only with the flag, and both can refuse the power-off.
- `GENPD_FLAG_MIN_RESIDENCY`: runtime only. `_default_power_down_ok()` compares
  state residency with the `next_wakeup` that devices set through
  `dev_pm_genpd_set_next_wakeup()`. The next hrtimer is read by
  `cpu_power_down_ok()`, under `GENPD_FLAG_CPU_DOMAIN`.

**Locks and callback context**

- Lock kinds: three. `genpd_lock_init()` tests `GENPD_FLAG_CPU_DOMAIN` first.

| Selected by | Lock | `lock_ops` |
|---|---|---|
| `GENPD_FLAG_CPU_DOMAIN`, with or without `GENPD_FLAG_IRQ_SAFE` | `raw_slock` | `genpd_raw_spin_ops` |
| `GENPD_FLAG_IRQ_SAFE` alone | `slock` | `genpd_spin_ops` |
| neither | `mlock` | `genpd_mtx_ops` |

- There is no genpd_lock_ops_spin in this tree.
- `raw_slock` domain: `power_on`, `power_off` and the notifiers run with IRQs
  off; for `slock` that holds only without `CONFIG_PREEMPT_RT`.
- `GENPD_FLAG_CPU_DOMAIN` without `GENPD_FLAG_IRQ_SAFE`: the lock is a raw
  spinlock but `genpd_is_irq_safe()` is false, so `genpd_switch_state()`,
  `genpd_add_subdomain()` and `irq_safe_dev_in_sleep_domain()` treat the domain
  as one that may sleep. The two providers that set the CPU flag,
  `drivers/cpuidle/cpuidle-psci-domain.c` and
  `drivers/cpuidle/cpuidle-riscv-sbi.c`, set both flags.
- Noirq system sleep: `genpd_finish_suspend()` and `genpd_finish_resume()` take
  the domain lock and pass `use_lock` true.
- Lockless path: `genpd_switch_state()`, behind `dev_pm_genpd_suspend()` and
  `dev_pm_genpd_resume()`. It sets `use_lock = genpd_is_irq_safe(genpd)`.
- Domain with `GENPD_FLAG_IRQ_SAFE` on that path: locked as usual.
- Domain without `GENPD_FLAG_IRQ_SAFE` on that path: no lock on the domain, nor
  on any parent reached from it, whatever the parent's own flags; `use_lock` is
  passed up unchanged.
- Context of the lockless path: a mutex domain's callbacks and notifiers can run
  with IRQs off there; for example `sh_cmt_clocksource_suspend()` in
  `drivers/clocksource/sh_cmt.c` is reached from
  `timekeeping_syscore_suspend()`.

**Per-device callback context**

- `set_hwmode_dev`: the one per-device callback called with the domain lock
  held, in `dev_pm_genpd_set_hwmode()`.
- `get_hwmode_dev`: called in `genpd_add_device()` before `genpd_lock()`.
- `attach_dev` and `get_hwmode_dev`: run under the global mutex `gpd_list_lock`,
  which every caller of `genpd_add_device()` holds. Calling `pm_genpd_init()` or
  `pm_genpd_add_subdomain()` from them deadlocks.
- `detach_dev`: no caller of `genpd_remove_device()` holds `gpd_list_lock`.
- `GENPD_FLAG_PM_CLK`: `pm_genpd_init()` assigns only `dev_ops.stop` and
  `dev_ops.start`, unconditionally. It does not touch `attach_dev` or
  `detach_dev`.
- Without `CONFIG_PM_CLK`: `pm_clk_suspend` and `pm_clk_resume` are defined as
  `NULL` in `include/linux/pm_clock.h`, so the flag clears both callbacks.

**Parent and child domains**

- `sd_count` at zero is not enough for the parent to power off:
  `genpd_power_off()` and `genpd_sync_power_off()` also return if any child has
  `state_idx < state_count - 1`. A child that is off in a shallower state keeps
  the parent on.
- Parent off and child on: `genpd_add_subdomain()` returns `-EINVAL`. It does
  not power the parent on.
- Duplicate link: `-EINVAL`.
- Flags read by `genpd_add_subdomain()`: only `GENPD_FLAG_IRQ_SAFE`. It has no
  test of `GENPD_FLAG_ALWAYS_ON`, and none of `GENPD_FLAG_CPU_DOMAIN`, so it
  does not compare lock kinds.
- **Potentially unsafe usage**: `pm_genpd_remove()` on a domain still linked to
  a parent.
  - Unsafe: when the domain is on and the parent stays registered.
    `genpd_remove()` frees the `child_links` without `genpd_sd_counter_dec()`,
    and `genpd_power_off()` of the parent then returns early on `sd_count`.
  - Safe: unlink first with `pm_genpd_remove_subdomain()`, which decrements for
    a child that is on; `scmi_pm_domain_remove()` does this through
    `of_genpd_remove_child_ids()`, which skips a parent whose provider is no
    longer registered.
  - Safe: the parent is removed in the same unwind, after its children, as
    `scpsys_domain_cleanup()` in `drivers/pmdomain/mediatek/mtk-pm-domains.c`
    does; `genpd_remove()` does not read `sd_count`.
- Device tree property: `power-domains-child-ids`, beside `power-domains` in
  the provider node; binding in
  `Documentation/devicetree/bindings/power/power-domain.yaml`.
- Parser: `of_genpd_add_child_ids()` in `drivers/pmdomain/core.c`.
  `of_genpd_add_provider_onecell()` does not call it. The provider calls it
  after registering, as `scmi_pm_domain_probe()` does, and undoes it with
  `of_genpd_remove_child_ids()`.
- Child id: indexes `data->domains[]` directly; the provider's `xlate` is not
  used for the child.
- `of_genpd_add_child_ids()` returns: the number of links on success, 0 when
  either property is absent, `-EINVAL` when the two counts differ. A parent
  that is not registered yet gives `-ENOENT`; `of_genpd_add_subdomain()` maps
  that to `-EPROBE_DEFER`, `of_genpd_add_child_ids()` does not.
- `of_genpd_add_child_ids()` on failure: removes the links it had already
  added.

## Boot-time state and sync_state

**Domains left on from boot**

- `genpd_power_off()` in `drivers/pmdomain/core.c`: is `void`; with `stay_on`
  set it returns silently, there is no error code for a caller to see.
- `genpd_set_stay_on()`: sets `stay_on` to `!is_off` only under
  `CONFIG_PM_GENERIC_DOMAINS_OF` and without `GENPD_FLAG_NO_STAY_ON`;
  otherwise `stay_on` is false.
- `GENPD_FLAG_NO_STAY_ON` and `GENPD_FLAG_NO_SYNC_STATE`: both exist, in
  `include/linux/pm_domain.h`.
- `GENPD_FLAG_NO_STAY_ON`: read once, in `pm_genpd_init()`; setting it
  after that call has no effect.
- Clearing sites: `of_genpd_sync_state()` and the `GENPD_SYNC_STATE_SIMPLE`
  case of `genpd_provider_sync_state()`; after `pm_genpd_init()` no other
  code writes `stay_on`.
- Both clearing sites call `genpd_power_off()` directly under the genpd
  lock; they do not call `genpd_queue_power_off_work()`.
- A domain registered on and never passed to
  `of_genpd_add_provider_simple()` or `of_genpd_add_provider_onecell()`:
  `stay_on` is still set by `pm_genpd_init()`, and nothing clears it.

**Provider sync_state wiring**

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

**Timing of sync_state**

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

**Powering off unused domains**

- `GENPD_FLAG_RPM_ALWAYS_ON`: `genpd_power_off()` returns for it
  unconditionally, with or without an active device.
- `pd_ignore_unused`: read only in `genpd_power_off_unused()`;
  `of_genpd_sync_state()` and runtime PM still power domains off with the
  option given.
- `GENPD_FLAG_NO_STAY_ON` in `rockchip_pm_add_one_domain()`: the tree gives
  no reason for it; nothing in the tree ties it to the regulator cleanup.
- There is no pm_domain_always_on command line option; the only option in
  `drivers/pmdomain/` is `pd_ignore_unused`.

**Driver-specific sync_state callbacks**

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

**Initial state and bootloader handover**

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

## Power transitions

**Runtime power-off conditions**

- `genpd_power_off()` in `drivers/pmdomain/core.c`: returns `void`; every
  decline is a bare `return`, no `-EBUSY` or `-EAGAIN` reaches a caller.
- Conditions that make it return before the provider is called, in order:
  1. `!genpd_status_on(genpd)`
  2. `genpd->prepared_count > 0`
  3. `GENPD_FLAG_ALWAYS_ON` or `GENPD_FLAG_RPM_ALWAYS_ON`
  4. `genpd->stay_on`
  5. `atomic_read(&genpd->sd_count) > 0`
  6. a subdomain on `parent_links` with
     `child->state_idx < child->state_count - 1`
  7. a device on `dev_list` with `rpm_always_on` set in its
     `struct generic_pm_domain_data` (set by `dev_pm_genpd_rpm_always_on()`)
  8. more than one device counted as not suspended, or one when `one_dev_on`
     is false; a device counts when `pm_runtime_suspended()` is false or
     `irq_safe_dev_in_sleep_domain()` is true
  9. `genpd->gov->power_down_ok()` returns false
  10. `sd_count > 0` again, after the governor
- `GENPD_FLAG_ACTIVE_WAKEUP`, `device_may_wakeup()` and `device_awake_path()`:
  not tested by `genpd_power_off()`.
- Governor with no `power_down_ok`: `genpd->state_idx` keeps its last value;
  it is reset to 0 only when `genpd->gov` is NULL.
- Declines 1 to 10: counted nowhere; `genpd->status` is not changed.
- Provider refusal: `_genpd_power_off()` returns non-zero both for a
  `GENPD_NOTIFY_PRE_OFF` notifier veto and for a `genpd->power_off()` error.
- On provider refusal: `genpd_power_off()` increments `rejected` of
  `genpd->states[genpd->state_idx]`, discards the error code, leaves the status
  on and does not touch the parents.
- `rejected`: readable in the debugfs file `idle_states`, printed by
  `idle_states_show()`.
- Callers in `drivers/pmdomain/core.c`: none reads `genpd->status` after the
  call; `genpd_runtime_suspend()` returns 0 whether or not the domain went
  off.
- Consumer that needs the outcome: `dev_pm_genpd_is_on()`, or a notifier from
  `dev_pm_genpd_add_notifier()`; `_genpd_power_off()` sends `GENPD_NOTIFY_OFF`
  only on success, `GENPD_NOTIFY_ON` follows a failed `genpd->power_off()`.

**Governors**

| Governor | `power_down_ok` (runtime) | `system_power_down_ok` |
|---|---|---|
| `simple_qos_governor` | `default_power_down_ok()` | not set |
| `pm_domain_always_on_gov` | not set | not set |
| `pm_domain_cpu_gov` | `cpu_power_down_ok()` | `cpu_system_power_down_ok()` |

- `pm_domain_always_on_gov`: there is no always_on_power_down_ok() or
  always-on callback here; the governor holds only `.suspend_ok`.
- `suspend_ok`: a per-device runtime-suspend check, called only from
  `genpd_runtime_suspend()`; it is not consulted at system suspend.
- `genpd_sync_power_off()`: calls `system_power_down_ok` when the governor has
  one, and leaves the domain on if it returns false.
- Governor without `system_power_down_ok`, or no governor: system suspend uses
  `genpd->state_count - 1`.
- `cpu_system_power_down_ok()` on a domain without `GENPD_FLAG_CPU_DOMAIN`:
  picks the deepest state and returns true.
- `cpu_system_power_down_ok()` on a CPU domain: picks the deepest state whose
  `power_off_latency_ns + power_on_latency_ns` fits
  `cpu_wakeup_latency_qos_limit()`; returns false if none fits.
- `cpu_power_down_ok()`: does not call `tick_nohz_get_next_hrtimer()`; it reads
  `next_hrtimer` of the `struct cpuidle_device` of each online CPU in
  `genpd->cpus`.
- `cpu_power_down_ok()` latency bound: the minimum of `cpu_latency_qos_limit()`,
  `cpu_wakeup_latency_qos_limit()` and the `dev_pm_qos_raw_resume_latency()`
  of each of those CPUs.
- `cpu_power_down_ok()`: returns false when `cpus_peek_for_pending_ipi()` is
  true for `genpd->cpus`, even if a state fits.
- `default_power_down_ok()`: weighs `residency_ns` only when the domain has
  `GENPD_FLAG_MIN_RESIDENCY` and some next wakeup is set; otherwise only
  off-plus-on latency against the QoS constraints.
- Domain given `pm_domain_always_on_gov`: `pm_genpd_init()` sets
  `GENPD_FLAG_RPM_ALWAYS_ON`, not `GENPD_FLAG_ALWAYS_ON`.
- Same domain at system suspend: `genpd_sync_power_off()` can power it off, to
  the deepest state.
- Same domain at runtime: governor data is still allocated and
  `default_suspend_ok()` still runs for each device runtime suspend.

**Data kept for governors**

- Default power state: `genpd_alloc_data()` sets it up when `state_count == 0`,
  with or without a governor.
- `struct genpd_governor_data`: there is no last_enable field; the field is
  `last_enter`.
- Device latency: measured in `genpd_runtime_suspend()` and
  `genpd_runtime_resume()` only when `td` is set and `pm_runtime_enabled(dev)`.
- Provider latency: `_genpd_power_off()` and `_genpd_power_on()` time the
  callback only when `timed` is true, `genpd->gd` is set and the state's
  `fwnode` is NULL.
- `genpd_sync_power_off()` and `genpd_sync_power_on()`: pass `timed` false, so
  they never update the provider latencies.
- `genpd_reflect_residency()` (`CONFIG_DEBUG_FS`): updates the `above` and
  `below` counters only when `genpd->gd` is set and `reflect_residency` is
  true; only `cpu_power_down_ok()` sets that.
- **Potentially unsafe usage**: dereferencing `genpd->gd` or `gpd_data->td`
  with no NULL test.
  - Unsafe: in code that runs for a domain registered with a NULL governor;
    `genpd_alloc_data()` and `genpd_alloc_dev_data()` leave both NULL.
  - Unsafe: for another domain's `gd`, since a parent or subdomain may have no
    governor.
  - Safe: in a governor callback, for the domain's own data, as
    `default_suspend_ok()` does; the callback runs only when `genpd->gov` is
    set.
  - Safe: `genpd->gd` inside a test of `td`, as `genpd_runtime_suspend()` does;
    `genpd_add_device()` allocates `td` only when `genpd->gd` is set.
  - Safe: after a test of the other domain's pointer, as
    `__default_power_down_ok()` does with `link->child->gd`.

**Runtime PM through a domain**

- `suspend_ok`: called only when `pm_runtime_enabled(dev)`; with runtime PM
  disabled the governor check is skipped.
- Suspend, under the domain lock: `genpd_power_off()` runs first, then
  `genpd_drop_performance_state()`.
- Resume, under the domain lock: `genpd_restore_performance_state()` runs
  first, then `genpd_power_on()`.
- Provider `set_performance_state`: can be called while the domain is
  `GENPD_STATE_OFF`, because of that order; nothing on the path tests the
  status.
- IRQ-safe device in a domain without `GENPD_FLAG_IRQ_SAFE`: the domain lock,
  power-off, power-on and the performance-state drop and restore are all
  skipped; the device's vote stays in force while it is suspended.
- Same device: the governor check, the device callbacks and
  `genpd_stop_dev()` and `genpd_start_dev()` still run.

**Performance state aggregation**

- Powered-off subdomain: its `link->performance_state` still counts;
  `_genpd_reeval_performance_state()` tests no status, and neither
  `genpd_power_off()` nor `genpd_sync_power_off()` writes the link field.
- Runtime-suspended device: its vote is zeroed by
  `genpd_drop_performance_state()`, not by
  `genpd_dev_pm_set_performance_state()`.
- `genpd_dev_pm_set_performance_state()` on a `pm_runtime_suspended()` device:
  only stores the value in `rpm_pstate`; the domain is not changed until
  resume.
- Device suspended by system sleep and not runtime suspended: keeps its vote;
  `genpd_finish_suspend()` does not touch performance states.
- Translation to a parent: there is no parent_performance_state field;
  `genpd_xlate_performance_state()` does it.
- Parent without `set_performance_state`: `genpd_xlate_performance_state()`
  passes the child's state through untranslated.
- Domain without `set_performance_state`: still records
  `genpd->performance_state` and still propagates to its parents.
- Several parents: `_genpd_set_performance_state()` walks `child_links` forward
  when the state goes up and in reverse when it goes down;
  `_genpd_set_parent_state()` handles one link.

**System suspend and resume**

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

**Boot protection at system sleep**

- `genpd_sync_power_off()`: does not read `genpd->stay_on`; a domain still
  under boot protection is powered off at system suspend like any other.
- `GENPD_FLAG_ALWAYS_ON`: the only keep-on setting that
  `genpd_sync_power_off()` honours.
- `stay_on` domain with no devices attached: reached as the parent of a
  subdomain that powers off, and passes the count test as 0 == 0.
- `genpd_power_off_unused()`: does not clear `stay_on`; it only queues
  `power_off_work`, and `genpd_power_off()` then returns for a `stay_on`
  domain.

## Provider drivers

**Registering a provider**

- Enforced order: only `pm_genpd_init()` first. Provider registration tests
  `genpd_present()`; link-before-register is not checked anywhere.
- `pm_genpd_add_subdomain()`: has no `genpd_present()` test and locks both
  domains through `lock_ops`, which `pm_genpd_init()` sets.
- Linking after registration: `genpd_add_subdomain()` returns `-EINVAL` when
  the parent is off and the subdomain is on; `__genpd_dev_pm_attach()` can
  power the subdomain on once the provider is visible.
- `of_genpd_add_child_ids()`: a third way to link. It takes children from
  `data->domains` and parents from `genpd_get_from_provider()`, so the parent's
  provider must be registered; `scmi_pm_domain_probe()` calls it after
  `of_genpd_add_provider_onecell()`.
- Per-domain check: there is no pm_genpd_present() here; it is static
  `genpd_present()` in `drivers/pmdomain/core.c`, which takes `gpd_list_lock`
  itself. Onecell does not hold that lock across its loop.
- Empty slot: `of_genpd_add_provider_onecell()` skips a NULL entry of
  `data->domains`, in the registration loop and in the unwind.
- `genpd_set_default_power_state()`: not called by onecell; `genpd_alloc_data()`
  calls it from `pm_genpd_init()` when `state_count` is 0.
- After any failed `of_genpd_add_provider_onecell()`: no domain in the array
  has `has_provider` set and each added `genpd->dev` has had `device_del()`, so
  `pm_genpd_remove()` needs no `of_genpd_del_provider()` first.

**Earliest provider registration**

- Both functions: return `-ENODEV` while `genpd_bus_registered` is false. The
  test is at the same place in both, right after the NULL-argument test and
  before `genpd_present()`.
- `genpd_bus_init()`: sets the flag only if all its registrations succeed; if
  it fails, both functions return `-ENODEV` for the rest of the boot.
- `core.o` is listed last in `drivers/pmdomain/Makefile`, after every vendor
  directory, so a `core_initcall()` in a vendor directory is linked ahead of
  `genpd_bus_init()`.
- `pm_genpd_init()` and `pm_genpd_add_subdomain()`: do not test
  `genpd_bus_registered`.
- **Potentially unsafe usage**: registering a provider from code that can run
  before `genpd_bus_init()`.
  - Unsafe: from an `early_initcall()` or a `CLK_OF_DECLARE()` init function;
    the call returns `-ENODEV`, not `-EPROBE_DEFER`, and nothing retries it.
  - Safe: initialise and link early, register from a later initcall, as
    `rcar_sysc_pd_init()` and `rcar_sysc_pd_init_provider()` in
    `drivers/pmdomain/renesas/rcar-sysc.c` do; `cpg_mstp_pd_init_provider()` in
    `drivers/clk/renesas/clk-mstp.c` is the same split.
  - Safe: a `core_initcall()` that only registers a platform driver, for
    example `exynos4_pm_init_power_domain()`, when the device is probed after
    `genpd_bus_init()` has run.

**Removing a provider**

- `genpd_remove()` returns `-EINVAL` only for a NULL or `ERR_PTR` argument.
  It does not test `gpd_list` membership; its next step is `genpd_lock()`
  through `lock_ops`.
- `has_provider` set: `-EBUSY`, tested before the other two conditions.
- Field names: there is no master_links; links are `parent_links` (this domain
  is the parent) and `child_links`. The device test is on `device_count`; the
  list itself is `dev_list`.
- `genpd->dev`: `of_genpd_del_provider()` does the `device_del()`;
  `genpd_remove()` only reaches `put_device()` in `genpd_free_data()`.
- `of_genpd_del_provider()` with no provider registered for `np`: changes
  nothing, so `has_provider` stays set.
- `genpd_remove()` frees the entries on the domain's own `child_links`, so a
  link to its parent never causes `-EBUSY`; only `parent_links` does.
- Unlinking before removal, in tree: `gdsc_unregister()` in
  `drivers/clk/qcom/gdsc.c` calls `of_genpd_del_provider()`, then
  `pm_genpd_remove_subdomain()` through `gdsc_pm_subdomain_remove()` for each
  domain that `gdsc_register()` linked to a parent, then `pm_genpd_remove()`.
- `of_genpd_remove_last()`: does not delete the provider and does not count
  domains. It runs `genpd_remove()` on the first `gpd_list` entry whose
  `provider` matches, which is the most recently initialised one.
- `of_genpd_remove_last()` stops at that first match even when removal fails,
  and returns the error as an `ERR_PTR`. In a loop, one busy domain ends the
  loop with the older domains still registered.

**Provider probe and remove**

- **Unsafe usage**: `pm_genpd_remove()` on a domain for which
  `pm_genpd_init()` did not return 0.
  - Safe: a NULL slot; `genpd_remove()` returns `-EINVAL` for it, as the unwind
    loop of `th1520_pd_probe()` relies on for disabled domains.
  - Safe: unwind only the domains whose init succeeded, as `imx93_pd_probe()`
    does by jumping past `pm_genpd_remove()` when init fails.
- **Potentially unsafe usage**: freeing a domain after `pm_genpd_remove()`
  without looking at the result.
  - Unsafe: when `has_provider` is set, `device_count` is not 0 or
    `parent_links` is not empty; the call returns `-EBUSY` and the domain stays
    on `gpd_list`.
  - Safe: in a probe error path where provider registration failed and the
    driver linked no subdomain under this domain, as `imx93_pd_probe()`;
    none of the three conditions in `genpd_remove()` can hold.
  - Safe: free only on success, as `psci_pd_remove()` in
    `drivers/cpuidle/cpuidle-psci-domain.c` does with the result of
    `of_genpd_remove_last()`.
- Writes after `pm_genpd_init()`: the core checks none. What matters is when
  each member is read.
- Consumed inside `pm_genpd_init()`, so a later write does not redo the step:
  `GENPD_FLAG_IRQ_SAFE` and `GENPD_FLAG_CPU_DOMAIN` for the lock type (in
  `genpd_lock_init()`), `GENPD_FLAG_PM_CLK`, `GENPD_FLAG_DEV_NAME_FW`,
  `GENPD_FLAG_NO_STAY_ON`, `name` for the device name (set by
  `dev_set_name()`), `state_count` of 0 for the default state.
- Overwritten by `pm_genpd_init()`, so a value set before it is lost: for
  example `gov` (replaced by the argument), `status`, and the `domain.ops`
  members it assigns. Other `domain.ops` members survive;
  `ti_sci_pm_domain_probe()` sets `suspend` there before init.
- Read at call time: `power_on`, `power_off`, `attach_dev`, `detach_dev`,
  `set_performance_state`. `set_performance_state` and
  `GENPD_FLAG_OPP_TABLE_FW` are also read at provider registration.
- Post-init write seen in tree: the lock class of `mlock`, with
  `lockdep_set_class()` in `imx93_blk_ctrl_probe()`; it has to follow init,
  which initialises the mutex.
- **Unsafe usage**: `pm_genpd_init()` again on a structure that
  `pm_genpd_remove()` released, without clearing it.
  - Unsafe: `genpd_free_data()` frees the default state but leaves `states`,
    `state_count` and `free_states` set, and `genpd_alloc_data()` allocates a
    new one only when `state_count` is 0. `device_initialize()` then reaches
    `kobject_init()`, which logs an already-initialised object.
  - Safe: a fresh zeroed structure for each probe, as `imx93_pd_probe()` gets
    from `devm_kzalloc()`.
- One domain, complete pair: `imx93_pd_probe()` and `imx93_pd_remove()` in
  `drivers/pmdomain/imx/imx93-pd.c`; `imx_pgc_domain_probe()` and
  `imx_pgc_domain_remove()` in `drivers/pmdomain/imx/gpcv2.c` have the same
  shape.
- Several domains with subdomain links: `imx93_blk_ctrl_probe()` in
  `drivers/pmdomain/imx/imx93-blk-ctrl.c` adds a `devm_add_action_or_reset()`
  after each step and has no `.remove`; devres unwinds provider, links, then
  domains, on probe failure and on unbind.
- `imx8m_blk_ctrl_probe()`: labels `cleanup_provider` and `cleanup_pds` plus
  `imx8m_blk_ctrl_remove()` are also complete for provider and domains.
- `drivers/pmdomain/mediatek/mtk-pm-domains.c`: has no `.remove` and never
  calls `of_genpd_del_provider()`; it is not an example of a remove path.
- None of these remove paths looks at the result of `pm_genpd_remove()`.

## Consumer devices

**Attaching one domain**

| Flag | Read by | Effect |
|---|---|---|
| `PD_FLAG_ATTACH_POWER_ON` | `dev_pm_domain_attach()`, passed as `power_on` to `acpi_dev_pm_attach()` only | ACPI: device put in D0. DT: not passed on |
| `PD_FLAG_DETACH_POWER_OFF` | `dev_pm_domain_attach()` | saved in `dev->power.detach_power_off`, only if `dev->pm_domain` is set after the attach |

- `dev_pm_domain_attach()`: reads no other flag; `PD_FLAG_NO_DEV_LINK`,
  `PD_FLAG_DEV_LINK_ON` and `PD_FLAG_REQUIRED_OPP` are read only by
  `dev_pm_domain_attach_list()`.
- `genpd_dev_pm_attach()`: takes no flags and always powers the domain on,
  also for callers that pass 0, such as `sdio_bus_probe()`.
- `dev->power.detach_power_off`: passed to `dev_pm_domain_detach()` by
  `device_unbind_cleanup()`; `acpi_dev_pm_detach()` acts on it,
  `genpd_dev_pm_detach()` ignores its `power_off` argument.
- `genpd_dev_pm_attach()` returns 0 when the number of `power-domains`
  entries is not exactly 1.
- Provider not registered: there is no of_genpd_get_from_provider() here;
  `genpd_get_from_provider()` fails and `__genpd_dev_pm_attach()` returns
  `driver_deferred_probe_check_state()`.
- `driver_deferred_probe_check_state()` once `initcalls_done` is set:
  `-ENODEV` without `CONFIG_MODULES`, `-ETIMEDOUT` when
  `driver_deferred_probe_timeout` is 0; `-EPROBE_DEFER` in every other case.
- `__genpd_dev_pm_attach()`: sets only `->detach` and `->sync` of the
  `struct dev_pm_domain`; `->start` and `->set_performance_state` are set
  in `pm_genpd_init()`.

**Single attach caller**

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

**Attaching several domains**

- `dev->pm_domain` already set: `dev_pm_domain_attach_by_id()` and
  `dev_pm_domain_attach_by_name()` return `ERR_PTR(-EEXIST)`,
  `dev_pm_domain_attach_list()` returns `-EEXIST`.
- **Potentially unsafe usage**: treating every negative return of
  `dev_pm_domain_attach_list()` or `devm_pm_domain_attach_list()` as fatal.
  - Unsafe: when the device may have exactly one `power-domains` entry on a
    bus that calls `dev_pm_domain_attach()`; the bus attached it and the
    list attach returns `-EEXIST`.
  - Safe: accept `-EEXIST`, as `qcom_cc_really_probe()` does.
  - Safe: test `dev->pm_domain` first, as `imx_rproc_attach_pd()` does.
- `dev_pm_domain_attach_list()` returning 0 (no `of_node`, or no entries):
  `*list` is not written; `dev_pm_domain_detach_list()` accepts NULL.
- `genpd_dev_pm_attach_by_name()`: NULL when the name is not in
  `power-domain-names`; inside `dev_pm_domain_attach_list()` a NULL becomes
  `-ENODEV`.
- `genpd_dev_pm_attach_by_id()`: `ERR_PTR(-ENODEV)` while
  `genpd_bus_registered` is false; a missing provider gives the
  `driver_deferred_probe_check_state()` result as `ERR_PTR()`.
- `genpd_dev_pm_attach_by_id()` ends with `genpd_queue_power_off_work()`: a
  domain that was on before the attach can be powered off right after it.
- Powering through the virtual device: hold a runtime PM reference on it,
  as `qcom_pas_pds_enable()` does.
- Powering through a `DL_FLAG_PM_RUNTIME` link: the virtual device is
  resumed when the consumer runtime-resumes, see `__rpm_callback()`, and
  also on `pm_runtime_set_active()`, see `__pm_runtime_set_status()`.
- Link created with `DL_FLAG_STATELESS`: `device_link_add()` sets
  `DL_STATE_NONE` and does not resume the supplier unless
  `DL_FLAG_RPM_ACTIVE` is given, as `panfrost_pm_domain_init()` does.

**Attach list defaults**

- `PD_FLAG_ATTACH_POWER_ON` and `PD_FLAG_DETACH_POWER_OFF`: not read by
  `dev_pm_domain_attach_list()`; setting them in `pd_flags` changes nothing.
- `PD_FLAG_DEV_LINK_ON`: the only flag that powers the domain on at attach;
  no effect together with `PD_FLAG_NO_DEV_LINK`.
- `PD_FLAG_DEV_LINK_ON` power-on does not last: `__rpm_put_suppliers()` drops
  the link's reference when the consumer runtime-suspends or is set
  `RPM_SUSPENDED`; after that the domain follows the consumer.
- `PD_FLAG_NO_DEV_LINK`: exists under that name in
  `include/linux/pm_domain.h`; `pd_links[i]` stays NULL.
- `PD_FLAG_REQUIRED_OPP`: calls `dev_pm_opp_set_config()` with the virtual
  device as `required_dev` and the loop index as `required_dev_index`; no
  power change.
- With no flags each attach still applies the `required-opps` level for that
  index as the virtual device's default performance state; see
  `genpd_set_required_opp()`, called from `__genpd_dev_pm_attach()`.

**Consumer helpers**

- `dev` for a consumer with several domains: the virtual device, for example
  `pd_devs[i]`; the consumer's own `dev->pm_domain` is NULL.
- None of the helpers excludes a concurrent detach; `genpd_remove_device()`
  frees the `struct generic_pm_domain_data` that some of them read.

| Helper | Unattached `dev` | genpd lock | Requires of the caller |
|---|---|---|---|
| `dev_to_genpd_dev()` | `ERR_PTR(-EINVAL)` only if `dev->pm_domain` is NULL | no | `dev->pm_domain` must be a genpd, it is not tested; no `EXPORT_SYMBOL` |
| `dev_pm_genpd_set_performance_state()` | `-ENODEV` | yes | no provider callback needed; applied at once unless `pm_runtime_suspended()`, so also with runtime PM disabled |
| `dev_pm_genpd_add_notifier()` | `-ENODEV` | yes | one per device, else `-EEXIST`; callback runs under the genpd lock, except from `dev_pm_genpd_suspend()` and `dev_pm_genpd_resume()` on a domain without `GENPD_FLAG_IRQ_SAFE` |
| `dev_pm_genpd_remove_notifier()` | `-ENODEV` | yes | `-ENODEV` if none was added; `rpmh_rsc_pd_attach()` uses a devres action, which runs before the detach in `device_unbind_cleanup()` |
| `dev_pm_genpd_set_next_wakeup()` | no-op | no | no-op if the domain has no governor; read only for `GENPD_FLAG_MIN_RESIDENCY`, in `update_domain_next_wakeup()` |
| `dev_pm_genpd_get_next_hrtimer()` | `KTIME_MAX` | no | updated only by `cpu_power_down_ok()`; read it at `GENPD_NOTIFY_PRE_OFF`, as `rpmh_rsc_write_next_wakeup()` does |
| `dev_pm_genpd_synced_poweroff()` | no-op | yes | set after the domain is on: `_genpd_power_on()` clears it; only a provider that reads `synced_poweroff` acts, see `drivers/clk/qcom/gdsc.c` |
| `dev_pm_genpd_set_hwmode()` | `-ENODEV` | yes | `-EOPNOTSUPP` without `set_hwmode_dev`; power state is not checked |
| `dev_pm_genpd_get_hwmode()` | not checked, dereferences `dev->power.subsys_data` | no | caller must know `dev` is attached to a genpd |
| `dev_pm_genpd_rpm_always_on()` | `-ENODEV` | yes | does not power on; tested in `genpd_power_off()`, not in `genpd_sync_power_off()` |
| `dev_pm_genpd_is_on()` | `false` | yes | result is a snapshot |
| `dev_pm_genpd_suspend()`, `dev_pm_genpd_resume()` | no-op | only with `GENPD_FLAG_IRQ_SAFE` | caller excludes all other genpd activity otherwise; calls must pair, they count in `suspended_count`; stubs without `CONFIG_PM_GENERIC_DOMAINS_SLEEP` |

- **Unsafe usage**: calling a helper marked "yes" under genpd lock from a
  power notifier callback of the same domain.
  - Unsafe: every caller of `genpd_power_on()` and `genpd_power_off()` holds
    the genpd lock around the notifier chain, so the helper deadlocks.
  - Safe: `dev_pm_genpd_get_next_hrtimer()`, which takes no lock, as
    `rpmh_rsc_pd_callback()` reaches it through `rpmh_flush()`.
  - Safe: a callback that only signals, as `cxpd_notifier_cb()` does.

## Model gaps

### Other mistakes models make

- Models do not know that `of_genpd_sync_state()` holds `gpd_list_lock` across
  `genpd_power_off()`, so `power_off` and the notifiers run under it there.
  `genpd_provider_sync_state()` with `GENPD_SYNC_STATE_SIMPLE` does not hold
  it.
- Models take detach to always succeed. `genpd_remove_device()` returns
  `-EAGAIN` while `prepared_count > 0`; `genpd_dev_pm_detach()` retries with
  doubling `mdelay()` below `GENPD_RETRY_MAX_MS`, then logs and returns with
  the device still attached and a virtual device not unregistered.
- Models do not know that single-domain attach sets up required OPPs itself:
  `__genpd_dev_pm_attach()` calls `genpd_set_required_opp_dev()` when
  `num_domains == 1`, which returns 0 at once when the consumer node has
  `#power-domain-cells`.
- Models do not know `pm_genpd_inc_rejected()` (a provider whose `power_off`
  returned 0 moves one count from `usage` to `rejected`; used in
  `drivers/cpuidle/cpuidle-psci.c`) or `dev_to_genpd_dev()` (used in
  `drivers/opp/core.c`).
