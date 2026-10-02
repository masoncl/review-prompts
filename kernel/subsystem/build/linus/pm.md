# Power Management Subsystem

## Main structures

### Objects and how they relate

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

## Where to look

**Core files**

| Job | File | Header a driver includes | Easy to miss |
|---|---|---|---|
| Wakeup sources | `drivers/base/power/wakeup.c`; `drivers/base/power/wakeup_stats.c` for the `wakeup` class, one device per source | `include/linux/device.h` | `include/linux/pm_wakeup.h` has `#error` unless `_DEVICE_H_` is defined; `include/linux/device.h` includes it. `pm_wakeup_pending()`, `pm_system_wakeup()`, `pm_get_wakeup_count()` are defined in `drivers/base/power/wakeup.c` but declared in `include/linux/suspend.h` |
| Per-device sysfs attributes | `drivers/base/power/sysfs.c` | none for its functions; their prototypes are in `drivers/base/power/power.h` | `include/linux/pm.h` declares only `power_group_name` from this file. Drivers change the groups indirectly: `device_set_pm_not_required()` (`include/linux/device.h`), `pm_runtime_no_callbacks()` (`include/linux/pm_runtime.h`), `device_set_wakeup_capable()` (`include/linux/pm_wakeup.h`), `dev_pm_qos_expose_latency_limit()` and siblings (`include/linux/pm_qos.h`) |
| Device phases of system sleep | `drivers/base/power/main.c`; `pm_generic_` sleep callbacks in `drivers/base/power/generic_ops.c` | `include/linux/pm.h` | `dev_pm_set_driver_flags()` and `device_enable_async_suspend()` are inlines in `include/linux/device.h` |
| Suspend core | `kernel/power/suspend.c` (needs `CONFIG_SUSPEND`); `kernel/power/main.c` (needs `CONFIG_PM`) | `include/linux/suspend.h` | `register_pm_notifier()`, `lock_system_sleep()` and `pm_wq` are defined in `kernel/power/main.c`; `pm_wq` is declared in `include/linux/pm_runtime.h` |
| Device PM QoS | `drivers/base/power/qos.c` on top of `kernel/power/qos.c` | `include/linux/pm_qos.h` | `pm_qos_update_target()`, `pm_qos_update_flags()` and `pm_qos_read_value()` live in `kernel/power/qos.c`, which is always built; a change there changes device QoS too |
| Task freezer | `kernel/freezer.c` (per task: `freeze_task()`, `__refrigerator()`, `set_freezable()`); `kernel/power/process.c` (all tasks: `freeze_processes()`, `thaw_processes()`) | `include/linux/freezer.h` | `include/linux/freezer.h` has no wait helpers: `wait_event_freezable()` is in `include/linux/wait.h`, `kthread_freezable_should_stop()` in `include/linux/kthread.h`, `TASK_FREEZABLE` in `include/linux/sched.h` |
| Runtime PM; wake interrupts; hibernation core and image code | Models have these right | see `drivers/base/power/Makefile` and `kernel/power/Makefile` | `kernel/power/user.c` is built under `CONFIG_HIBERNATION_SNAPSHOT_DEV`, not `CONFIG_HIBERNATION` |

## Runtime PM helpers

**Wrapper to base function map**

- Last-busy refresh by the `RPM_AUTO` wrappers:

| Wrapper | Calls `pm_runtime_mark_last_busy()` itself |
|---|---|
| `pm_runtime_autosuspend()` | yes |
| `pm_request_autosuspend()` | yes |
| `pm_runtime_put_autosuspend()` | yes |
| `pm_runtime_put_sync_autosuspend()` | yes |
| `__pm_runtime_put_autosuspend()` | no |

- `__pm_runtime_put_autosuspend()`: defined in `include/linux/pm_runtime.h`;
  same flags as `pm_runtime_put_autosuspend()`, which calls it.
- Wrappers that reach `__pm_runtime_idle()` (`pm_runtime_idle()`,
  `pm_request_idle()`, `pm_runtime_put()`, `pm_runtime_put_sync()`): honour
  the autosuspend delay although they pass no `RPM_AUTO`, because `rpm_idle()`
  ends with `rpm_suspend(dev, rpmflags | RPM_AUTO)`.
- `pm_runtime_suspend()` and `pm_runtime_put_sync_suspend()`: the two wrappers
  that reach `rpm_suspend()` without `RPM_AUTO`, so they ignore the delay.
- `pm_runtime_autosuspend()` and `pm_runtime_put_sync_autosuspend()`: have no
  `RPM_ASYNC`, but they refresh last-busy first, so with autosuspend in use
  and a positive delay `rpm_suspend()` arms `dev->power.suspend_timer` and
  returns 0 instead of running the `runtime_suspend` callback in the caller.

**Scope-based helpers**

- Guard classes in `include/linux/pm_runtime.h`:

| Class | Entry | Exit | Acquire macro |
|---|---|---|---|
| `pm_runtime_noresume` | `pm_runtime_get_noresume()` | `pm_runtime_put_noidle()` | none |
| `pm_runtime_active` | `pm_runtime_get_sync()`, result dropped | `pm_runtime_put()` | none |
| `pm_runtime_active_auto` | `pm_runtime_get_sync()`, result dropped | `pm_runtime_put_autosuspend()` | none |
| `pm_runtime_active_try` | `pm_runtime_get_active()` with `RPM_TRANSPARENT` | `pm_runtime_put()` | `PM_RUNTIME_ACQUIRE()` |
| `pm_runtime_active_try_enabled` | `pm_runtime_resume_and_get()` | `pm_runtime_put()` | `PM_RUNTIME_ACQUIRE_IF_ENABLED()` |
| `pm_runtime_active_auto_try` | `pm_runtime_get_active()` with `RPM_TRANSPARENT` | `pm_runtime_put_autosuspend()` | `PM_RUNTIME_ACQUIRE_AUTOSUSPEND()` |
| `pm_runtime_active_auto_try_enabled` | `pm_runtime_resume_and_get()` | `pm_runtime_put_autosuspend()` | `PM_RUNTIME_ACQUIRE_IF_ENABLED_AUTOSUSPEND()` |

- `PM_RUNTIME_ACQUIRE_ERR()`: takes the address of the variable named in the
  acquire macro; it is defined on class `pm_runtime_active` and serves all
  four acquire macros; 0 on success, negative errno on failure.
- Failed conditional acquire: the reference is already dropped by
  `pm_runtime_get_active()` and the exit put is skipped.
- Runtime PM disabled, `_try` classes: `rpm_resume()` returns 0 without
  resuming, so the acquire succeeds and holds a reference while the device
  may be suspended.
- Runtime PM disabled, `_try_enabled` classes: `-EACCES`, except that they
  succeed when `runtime_status` and `last_status` are both `RPM_ACTIVE`.
- `last_status`: set by `__pm_runtime_disable()` to the status at that moment
  and reset to `RPM_INVALID` by `pm_runtime_enable()`, so `_try_enabled`
  fails before the first enable even after `pm_runtime_set_active()`.
- `dev->power.runtime_error` set: both kinds fail with `-EINVAL`, disabled or
  not; `rpm_resume()` tests it first.
- 0 from `PM_RUNTIME_ACQUIRE_ERR()`: for the `_try` classes it also covers
  "runtime PM disabled, nothing resumed, status possibly `RPM_SUSPENDED`";
  for the `_try_enabled` classes a disabled device gives 0 only in the
  both-`RPM_ACTIVE` case above.
- For example `acpi_tad_wake_set()` in `drivers/acpi/acpi_tad.c` uses
  `PM_RUNTIME_ACQUIRE()`; `sound/soc/codecs/cs42l43-jack.c` uses
  `PM_RUNTIME_ACQUIRE_IF_ENABLED_AUTOSUSPEND()`.

**Put helpers and their results**

- `pm_runtime_put()`: returns `void` in `include/linux/pm_runtime.h`; code
  that assigns or tests its result, or returns it from a function that is
  not `void`, does not compile.
- `__pm_runtime_put_autosuspend()`: returns `int`, like
  `pm_runtime_put_autosuspend()`.
- `Documentation/power/runtime_pm.rst`: still lists `int pm_runtime_put()`
  "and return its result"; the header is what compiles.
- Result 1: the status was already `RPM_SUSPENDED`; it comes from
  `rpm_check_suspend_allowed()`.
- `CONFIG_PM` off: the puts that return `int`, for example
  `pm_runtime_put_sync()` and `pm_runtime_put_autosuspend()`, return
  `-ENOSYS` from the stubs of `__pm_runtime_idle()` and
  `__pm_runtime_suspend()`, so a caller that propagates the result fails on
  such a kernel.
- `pm_runtime_put_sync()`: also returns any non-zero value of the
  `runtime_idle` callback, unchanged; see `rpm_idle()`.
- Synchronous puts: return the error of the `runtime_suspend` callback, with
  `-EACCES` turned into `-EAGAIN` by `rpm_callback()`; unless the result is
  `-EAGAIN` or `-EBUSY`, `rpm_suspend()` stores it in
  `dev->power.runtime_error` and later calls return `-EINVAL`.

**Usage counter after a failed get**

- Runtime PM disabled: `rpm_resume()` returns 1, not `-EACCES`, when
  `runtime_status` and `last_status` are both `RPM_ACTIVE`; then
  `pm_runtime_get_sync()` returns 1 and `pm_runtime_resume_and_get()`
  returns 0, each holding a reference.
- `pm_runtime_get_sync()` success is `>= 0`: 1 when the device was already
  active, and always 1 with `CONFIG_PM` off; `pm_runtime_resume_and_get()`
  returns only 0 or a negative errno.
- `pm_runtime_get()`: `-EINPROGRESS` means a resume is already running
  (`RPM_RESUMING`); the reference is held as for every other result.
- A put after a failed `pm_runtime_resume_and_get()`: see "Counter-only
  helpers" for what each put does at zero.

**Counter-only helpers**

- `rpm_drop_usage_count()` in `drivers/base/power/runtime.c`: does
  `atomic_sub_return(1, &dev->power.usage_count)`; on a negative result it
  increments again, logs "Runtime PM usage count underflow!" and returns
  `-EINVAL`.
- `pm_runtime_put_noidle()`: does not call `rpm_drop_usage_count()`; it is
  `atomic_add_unless(&dev->power.usage_count, -1, 0)`, so at zero it does
  nothing, with no warning and no return value.
- Neither path leaves the counter below zero.
- An unbalanced put while another holder exists: succeeds silently on both
  paths and takes that holder's reference.
- `pm_runtime_put()` at zero: returns `void`, so the underflow shows only as
  the warning.
- `pm_runtime_allow()`: also calls `rpm_drop_usage_count()`, as
  `__pm_runtime_idle()` and `__pm_runtime_suspend()` do for the puts.

**Conditional get and interrupt handlers**

- `pm_runtime_get_if_in_use()`: with the status `RPM_ACTIVE`, takes a
  reference and returns 1 when the usage counter is non-zero, and also when
  `dev->power.ignore_children` is clear and `child_count` is above zero,
  even with a usage counter of zero; see `pm_runtime_get_conditional()`.
- `Documentation/power/runtime_pm.rst`: describes
  `pm_runtime_get_if_in_use()` without the child condition.
- **Potentially unsafe usage**: testing the result only for non-zero, then
  touching the device and doing a put.
  - Unsafe: with `CONFIG_PM` on and runtime PM disabled, `-EINVAL` passes the
    test with no reference taken; a put other than `pm_runtime_put_noidle()`
    then makes `rpm_drop_usage_count()` warn of underflow, and any put can
    take another holder's reference.
  - Safe: with `CONFIG_PM` off; `pm_runtime_put_noidle()` is an empty stub and
    the other puts reach the stubs of `__pm_runtime_idle()` and
    `__pm_runtime_suspend()`, which touch no counter.
  - Safe: put only when the result is above zero, as `ipu6_buttress_isr()` in
    `drivers/media/pci/intel/ipu6/ipu6-buttress.c` does.
  - Safe: skip the access and the put on any result `<= 0`, as
    `mtk_iommu_tlb_flush_range_sync()` in `drivers/iommu/mtk_iommu.c` does.

**Register access in interrupt handlers**

- **Unsafe usage**: a handler that decides from `pm_runtime_suspended()` or
  `pm_runtime_active()` alone whether to touch registers; the first is false
  during `RPM_SUSPENDING` and whenever runtime PM is disabled, the second is
  true whenever it is disabled, and neither takes a reference.
  - Safe: touch registers only after `pm_runtime_get_if_in_use()` or
    `pm_runtime_get_if_active()` returned 1, then put, as `rk_iommu_irq()` in
    `drivers/iommu/rockchip-iommu.c` does on an `IRQF_SHARED` line;
    `pm_runtime_get_conditional()` tests `RPM_ACTIVE` under
    `dev->power.lock`, and `rpm_check_suspend_allowed()` refuses a suspend
    while the counter is non-zero.
  - Safe: test a driver flag that the suspend path sets before it calls
    `synchronize_irq()`, as `panfrost_gpu_irq_handler()` does with
    `PANFROST_COMP_BIT_GPU`; `panfrost_gpu_suspend_irq()` sets the bit, masks
    and synchronizes before `panfrost_gpu_power_off()`.
  - Safe: test a driver flag under a lock and make the register accesses
    before dropping that lock, as `sdhci_irq()` does with
    `host->runtime_suspended` for the accesses it makes under `host->lock`;
    `sdhci_runtime_suspend_host()` sets it under the same lock.
- Suspend callback run by `rpm_suspend()`, handler uses a conditional get:
  needs no `synchronize_irq()` for the handler's register access; a handler
  that got 1 blocks the suspend, and a handler that runs after
  `rpm_suspend()` set `RPM_SUSPENDING` gets 0; `rk_iommu_suspend()` has none.
- Suspend callback, handler uses a lockless flag: must set the flag first,
  then call `synchronize_irq()`, then cut power;
  `panfrost_device_runtime_suspend()` does so, and `intel_irq_suspend()` in
  `drivers/gpu/drm/i915/i915_irq.c` does the first two steps for
  `i915_pm_runtime_suspend()`.
- There is no intel_runtime_pm_disable_interrupts() in this tree;
  `intel_irq_suspend()` does that job, and handlers test
  `intel_irqs_enabled()`.
- `pm_runtime_get_if_in_use()` in a handler: returns 0 while the device is
  `RPM_ACTIVE` with a zero counter and no counted children, so it fits only
  a device that interrupts while a reference is held;
  `pm_runtime_get_if_active()`, as in `ipu6_buttress_isr()`, has no such
  limit.
- Result `-EINVAL` in a handler: `rk_iommu_irq()` returns without touching
  registers; `ipu6_buttress_isr()` goes on and skips the put.

**Autosuspend**

- `pm_runtime_autosuspend_expiration()`: returns `u64` nanoseconds on the
  `ktime_get_mono_fast_ns()` clock, not jiffies, and does no rounding.
- `Documentation/power/runtime_pm.rst`: still describes it as returning
  `unsigned long` jiffies rounded up to a second for long delays; the code
  in `drivers/base/power/runtime.c` does neither.
- Delay of 0: not tested for; the delay test is `autosuspend_delay < 0`, and
  a zero delay returns 0 because the expiry is not in the future.
- `dev->power.last_busy`: written by `pm_runtime_mark_last_busy()`, which
  `rpm_resume()` also calls on every successful resume.
- Negative delay with `use_autosuspend` set: on the change to that state
  `update_autosuspend()` increments `usage_count` and calls `rpm_resume()`;
  the held reference is what blocks suspend, through
  `rpm_check_suspend_allowed()`.
- Negative delay with `use_autosuspend` clear: `update_autosuspend()` takes
  no reference.
- `pm_runtime_dont_use_autosuspend()` after `pm_runtime_disable()`: still
  clears the flag and drops the negative-delay reference; only the
  `rpm_idle()` at its end fails with `-EACCES`.
- `pm_runtime_reinit()`: resets neither `use_autosuspend` nor
  `autosuspend_delay` on unbind.

**Asynchronous put before teardown**

- **Potentially unsafe usage**: `pm_runtime_put_sync()` dropping the last
  reference just before `pm_runtime_disable()` where the device must end up
  suspended.
  - Unsafe: while `use_autosuspend` is set and the delay has not expired;
    `rpm_idle()` adds `RPM_AUTO`, `rpm_suspend()` only arms the timer, and
    `__pm_runtime_barrier()` then cancels it, leaving the device active.
  - Safe: after `pm_runtime_dont_use_autosuspend()`, as `omap_i2c_remove()`
    in `drivers/i2c/busses/i2c-omap.c` does;
    `pm_runtime_autosuspend_expiration()` then returns 0.
  - Safe: with `pm_runtime_put_sync_suspend()` instead, as `hidma_remove()`
    in `drivers/dma/qcom/hidma.c` does; it passes no `RPM_AUTO`, see "Wrapper
    to base function map".
  - Safe: where the status is tested after the disable and power is cut by
    hand, as `ov5675_remove()` in `drivers/media/i2c/ov5675.c` does with
    `pm_runtime_status_suspended()` and `pm_runtime_set_suspended()`.
- `pm_runtime_dont_use_autosuspend()` with runtime PM enabled: ends in a
  synchronous `rpm_idle(dev, RPM_AUTO)`, so with a zero counter it can run
  the `runtime_suspend` callback in the caller.
- That `rpm_idle()` returns `-EAGAIN` and does nothing while a suspend,
  autosuspend or resume request is still queued.
- `__device_release_driver()` in `drivers/base/dd.c`: calls
  `pm_runtime_put_sync()` before `device_remove()`, so the remove callback
  runs with no reference held by the driver core.
- `__pm_runtime_disable()`: with `check_resume` true, as
  `pm_runtime_disable()` passes, runs a pending `RPM_REQ_RESUME` before it
  raises `disable_depth`; when `disable_depth` is already non-zero it only
  increments and calls no barrier.
- `__pm_runtime_barrier()`: stops the timer through
  `pm_runtime_deactivate_timer()`, which uses `hrtimer_try_to_cancel()`;
  calls `cancel_work_sync()` only when `dev->power.request_pending` is set.
- `pm_runtime_force_suspend()`: calls `pm_runtime_disable()` itself and
  returns with runtime PM still disabled on success, so a further
  `pm_runtime_disable()` raises `disable_depth` to 2.
- `pm_runtime_reinit()`: does not lower `disable_depth` on unbind.

## Runtime PM return values

**Resume path return values**

- `-EAGAIN` from `rpm_resume()`: never produced by its own tests; it is a
  callback value, or `-EACCES` from a callback converted in `rpm_callback()`.
- `power.no_callbacks`: gives `1` through the parent shortcut, and `0` when
  it resumes without the shortcut; no branch of `rpm_resume()` produces
  `-EPERM`.
- Parent: the sync path calls `rpm_resume(parent, 0)` when the parent has
  runtime PM enabled and `power.ignore_children` clear and the device is not
  `power.irq_safe`, and returns `-EBUSY` if the parent is not `RPM_ACTIVE`
  afterwards.
- `RPM_ASYNC`: leaves `rpm_resume()` before the parent step, so an async call
  never resumes the parent and never returns `-EBUSY`.
- Missing `->runtime_resume()`: `__rpm_callback()` skips a NULL callback and
  returns `0`; the status becomes `RPM_ACTIVE`.
- `-ENOSYS`: not produced by `drivers/base/power/runtime.c` for a missing
  callback.
- Supplier error: with `power.links_count > 0` and no `power.irq_safe`,
  `__rpm_callback()` returns the error of `rpm_get_suppliers()` and the
  callback is not run.
- `rpm_get_suppliers()`: ignores `-EACCES` from a supplier.
- Positive value from `->runtime_resume()`: `rpm_resume()` tests `if (retval)`,
  so the status goes back to `RPM_SUSPENDED` and the value is returned
  unchanged; a caller testing `< 0` reads it as success.
- Sync `0` with `RPM_TRANSPARENT`: can mean nothing was resumed; see "Calls
  while runtime PM is disabled".
- `-EINPROGRESS`: see "Concurrent transitions".
- Without `CONFIG_PM`: the stubs in `include/linux/pm_runtime.h` return `1`
  for `__pm_runtime_resume()` and `-ENOSYS` for `__pm_runtime_suspend()` and
  `__pm_runtime_idle()`.

**Suspend path return values**

- `RPM_GET_PUT`: `__pm_runtime_suspend()` calls `rpm_drop_usage_count()`, not
  `atomic_dec_and_test()`.
- `rpm_drop_usage_count()` on underflow: increments the counter back, warns
  and returns `-EINVAL`; `rpm_suspend()` is not called.
- `rpm_check_suspend_allowed()`: one else-if chain; see it for the order.
- `power.child_count` non-zero without `power.ignore_children`: `-EBUSY`, not
  `-EAGAIN`.
- `__dev_pm_qos_resume_latency()` equal to 0: `-EPERM`.
- `1` (already `RPM_SUSPENDED`): tested last, so a suspended device with a
  held reference gets `-EAGAIN`.
- `1`: returned for `RPM_ASYNC` and `RPM_AUTO` calls too.
- `RPM_RESUMING`: not tested by `rpm_check_suspend_allowed()`; `rpm_suspend()`
  tests it and returns `-EAGAIN` only without `RPM_ASYNC`.
- `RPM_AUTO` with an unexpired delay: returns `0`, not `-EAGAIN`.
- Autosuspend timer: armed in that branch whether or not `RPM_ASYNC` is set.
- `RPM_SUSPENDING` with `RPM_ASYNC` or `RPM_NOWAIT`: `-EINPROGRESS`, not
  `-EBUSY`.
- `RPM_ASYNC` request queued on `pm_wq`: returns `0`, not `-EINPROGRESS`.
- `-EAGAIN` after a successful callback: `power.deferred_resume` was set; see
  "Concurrent transitions".

**Idle path return values**

- Already `RPM_SUSPENDED`, with `RPM_GET_PUT`: `rpm_idle()` returns `1`, as
  `pm_runtime_put_sync()` does.
- Already `RPM_SUSPENDED`, without `RPM_GET_PUT`: `-EAGAIN`, as
  `pm_runtime_idle()` and `pm_request_idle()` do.
- `drivers/base/power/runtime-test.c`: `pm_runtime_already_suspended_test()`
  and `pm_runtime_idle_test()` pin both results.
- Usage counter: with `RPM_GET_PUT`, decremented by `rpm_drop_usage_count()`
  in `__pm_runtime_idle()` before `rpm_idle()` runs; `rpm_idle()` never
  changes it.
- Underflow: `__pm_runtime_idle()` returns `-EINVAL` without calling
  `rpm_idle()`.
- `-EINPROGRESS`: `power.idle_notification` is already set; it never means
  "queued".
- `RPM_ASYNC` with an idle callback: queues `RPM_REQ_IDLE` and returns `0`.
- `RPM_ASYNC` with no idle callback, or with `power.no_callbacks`: nothing is
  queued as `RPM_REQ_IDLE`; the result is that of
  `rpm_suspend(dev, rpmflags | RPM_AUTO)`.
- Idle callback: called as `callback(dev)`, not through `__rpm_callback()` or
  `rpm_callback()`, so `-EACCES` from it is returned unchanged.

**Calls while runtime PM is disabled**

- `RPM_TRANSPARENT`: defined in `include/linux/pm_runtime.h`; with it,
  `rpm_resume()` on a disabled device returns `0` where it would return
  `-EACCES`.
- Order in `rpm_resume()`: `power.runtime_error` (`-EINVAL`), then the `1`
  case (`power.runtime_status` and `power.last_status` both `RPM_ACTIVE`),
  then `RPM_TRANSPARENT`, then `-EACCES`.
- `0` from `RPM_TRANSPARENT`: nothing was resumed and the status is unchanged,
  so the device may be `RPM_SUSPENDED`.
- `pm_runtime_get_active()`: the only in-tree code that passes
  `RPM_TRANSPARENT`, for the guard classes `pm_runtime_active_try` and
  `pm_runtime_active_auto_try`.
- `pm_runtime_resume_and_get()`, `PM_RUNTIME_ACQUIRE_IF_ENABLED()` and
  `PM_RUNTIME_ACQUIRE_IF_ENABLED_AUTOSUSPEND()`: pass no `RPM_TRANSPARENT`
  and fail with `-EACCES` on a disabled device outside the `1` case, or with
  `-EINVAL` when `power.runtime_error` is set.
- `rpm_suspend()` and `rpm_idle()`: do not test `RPM_TRANSPARENT`; a disabled
  device gets `-EACCES` from `rpm_check_suspend_allowed()` whatever the flags,
  unless `power.runtime_error` is set, which gives `-EINVAL` first.

**Sticky callback errors**

- `power.runtime_error` is written with a callback result in one place: the
  `fail:` label of `rpm_suspend()`.
- `rpm_callback()`: does not touch `power.runtime_error`; it only converts
  `-EACCES` to `-EAGAIN`.
- `->runtime_resume()` failure: not recorded. `rpm_resume()` sets the status
  to `RPM_SUSPENDED` and returns the value; the next resume runs the callback
  again.
- `->runtime_suspend()` values recorded: every non-zero value other than
  `-EAGAIN`, `-EBUSY` and `-EACCES`, positive values included.
- Missing `->runtime_suspend()`: `__rpm_callback()` returns `0`; nothing is
  recorded and the status becomes `RPM_SUSPENDED`.
- `__pm_runtime_set_status()` with the field set: accepted while runtime PM is
  enabled; the device need not be disabled first.
- `__pm_runtime_set_status()` returning an error (parent not active, supplier
  activation failed): leaves the field set.
- `pm_runtime_init()`: zeroes the field.
- `pm_runtime_reinit()`: has no write of the field of its own; when the
  device is disabled and its status is `RPM_ACTIVE` it calls
  `pm_runtime_set_suspended()`, which clears the field.
- There is no pm_runtime_clean_up_links() in this tree.

**Concurrent transitions**

- `rpm_resume()` on `RPM_RESUMING` with `RPM_ASYNC` or `RPM_NOWAIT`:
  `-EINPROGRESS`.
- `rpm_resume()` on `RPM_SUSPENDING` with `RPM_NOWAIT`: sets
  `power.deferred_resume` and returns `-EINPROGRESS`.
- `rpm_resume()` on `RPM_SUSPENDING` with `RPM_ASYNC` and no `RPM_NOWAIT`:
  sets `power.deferred_resume` and returns `0`.
- `rpm_suspend()` on `RPM_RESUMING` without `RPM_ASYNC`: `-EAGAIN`, no wait;
  `RPM_NOWAIT` alone gets this too.
- `rpm_suspend()` on `RPM_RESUMING` with `RPM_ASYNC`: goes on to arm the timer
  or queue the request and returns `0`.
- `rpm_check_suspend_allowed()`: runs before any of the `rpm_suspend()` cases,
  so a held reference gives `-EAGAIN` first.
- Sync `rpm_suspend()` on `RPM_SUSPENDING` with `power.deferred_resume` set:
  `-EAGAIN` from the check, no wait.
- `power.irq_safe` devices: the wait is a loop of unlock, `cpu_relax()`, lock,
  not a sleep on `power.wait_queue`.
- `pm_runtime_work()`: passes `RPM_NOWAIT` for every request type, so a queued
  request that finds the device `RPM_SUSPENDING` or `RPM_RESUMING` returns
  instead of waiting.
- Deferred resume after a successful callback: `rpm_suspend()` first sets
  `RPM_SUSPENDED`, drops the parent's `power.child_count` and wakes waiters,
  then calls `rpm_resume(dev, 0)`.
- `-EAGAIN` from that path: the result of `rpm_resume(dev, 0)` is discarded,
  so `-EAGAIN` does not prove the device is active.
- Failed suspend callback: the `fail:` label clears `power.deferred_resume`
  without resuming; the status is already back to `RPM_ACTIVE`.

**Put and get races**

- `pm_runtime_put_sync()`: the put helper that returns the `rpm_idle()`
  result; in this race it returns `-EAGAIN`, unfiltered.
- `-EAGAIN` from a put: also returned for a pending resume request, a status
  of `RPM_SUSPENDING` or `RPM_RESUMING`, or a transient callback result; the
  value does not identify the race.
- `-EINVAL` from a put: usage counter underflow, `power.runtime_error` set,
  or a callback returning it; the value does not tell which.
- Repeating a put after `-EAGAIN`: while another holder exists it drops that
  holder's reference and can suspend the device under it.

## Runtime PM core

**Status values**

| Value | Stands for | `power.runtime_status` | `power.last_status` |
|---|---|---|---|
| `RPM_INVALID` | no saved status: runtime PM is enabled, or was never enabled | never | yes |
| `RPM_BLOCKED` | device was disabled and never enabled when `device_prepare()` ran; enabling it now warns | never | yes |
| `RPM_ACTIVE`, `RPM_SUSPENDED` | settled state | yes | yes, copied at disable |
| `RPM_RESUMING`, `RPM_SUSPENDING` | callback in progress | yes | never |

- `__pm_runtime_disable()`: runs `__pm_runtime_barrier()` before it copies
  `runtime_status` into `last_status`, so a transient value is never copied.
- `pm_runtime_enable()` when the depth reaches 0: sets `last_status` to
  `RPM_INVALID`; it does not restore `runtime_status` from it.
- `rpm_resume()` does not test `RPM_BLOCKED`; there is no `-EPERM` for it.
- `RPM_BLOCKED` readers: `pm_runtime_enable()`, `pm_runtime_unblock()` and
  `pm_runtime_blocked()`, which `device_prepare_smart_suspend()` in
  `drivers/base/power/main.c` calls.
- `__pm_runtime_set_status()` on a disabled device: writes `runtime_status`,
  not `last_status`; after `pm_runtime_set_active()` on a never-enabled device
  `last_status` is still `RPM_INVALID` and `rpm_resume()` returns `-EACCES`.

**Runtime PM state and its lock**

- `power.lock`: initialised by `device_pm_init_common()` in
  `drivers/base/power/power.h`, not by `pm_runtime_init()`.
- `pm_runtime_init()`: sets `power.runtime_auto` to true and clears
  `power.needs_force_resume`.
- `pm_runtime_init()`: does not write `irq_safe`, `no_callbacks`,
  `use_autosuspend`, `autosuspend_delay`, `last_busy` or `links_count`.
- `pm_runtime_active()`: true for every device with `disable_depth` non-zero,
  so true for a new device whose status is `RPM_SUSPENDED`.
- `pm_runtime_suspended()`: false for a disabled device;
  `pm_runtime_status_suspended()` ignores `disable_depth`.

| Member | Written | Read |
|---|---|---|
| `ignore_children` | plain store, no lock, in `pm_suspend_ignore_children()` | under the lock in `rpm_check_suspend_allowed()`; the parent's flag is read holding only the child's lock in `rpm_suspend()` |
| `no_callbacks` | under the lock in `pm_runtime_no_callbacks()`; plain store in `device_set_pm_not_required()` | under the lock in `rpm_idle()`, `rpm_suspend()` and `rpm_resume()` |
| `autosuspend_delay` | under the lock in `pm_runtime_set_autosuspend_delay()` | `READ_ONCE()`, lock not needed, in `pm_runtime_autosuspend_expiration()` |
| `last_busy` | `WRITE_ONCE()`, no lock | `READ_ONCE()`, no lock |
| `irq_safe` | under the lock | without the lock in the `might_sleep_if()` checks and `__rpm_callback()` |
| `last_status` | under the lock, except in `pm_runtime_init()` | without the lock in `pm_runtime_blocked()` |

- `child_count` of the parent: `rpm_suspend()`, the normal path of
  `rpm_resume()` and the `RPM_SUSPENDED` branch of
  `__pm_runtime_set_status()` change it holding only the child's
  `power.lock`.
- `child_count` under the parent's lock: only the `no_callbacks` shortcut in
  `rpm_resume()` and the `RPM_ACTIVE` branch of `__pm_runtime_set_status()`.
- `disable_depth`: a 3-bit field; `__pm_runtime_disable()` increments it with
  no range check, so an eighth nested disable wraps it to 0.
- `disable_depth`: `__pm_runtime_set_status()` also increments it, under the
  lock, and ends with `pm_runtime_enable()`.
- `usage_count`: `pm_runtime_forbid()` holds one count until
  `pm_runtime_allow()`; `update_autosuspend()` holds one while
  `use_autosuspend` is set and the delay is negative.
- `pm_runtime_get_noresume()`: does not stop a suspend that has passed
  `rpm_check_suspend_allowed()`; `rpm_suspend()` tests `usage_count` there,
  under the lock, and not again after the callback succeeds.
- `pm_runtime_get_if_active()` and `pm_runtime_get_if_in_use()`: return
  `-EINVAL` with the count unchanged when `disable_depth` is non-zero; only a
  return of 1 means a count is held.
- **Potentially unsafe usage**: testing `power.runtime_status` without
  `power.lock` and acting on the result.
  - Unsafe: with runtime PM enabled, while another task can start a suspend
    or resume; a count taken with `pm_runtime_get_noresume()` just before the
    test does not prevent it.
  - Safe: with `power.lock` held across the test and the action, as
    `pci_dev_adjust_pme()` in `drivers/pci/pci.c` does; every caller of
    `__update_runtime_status()` holds the lock.
  - Safe: `pm_runtime_get_if_active()`, which tests the status and takes the
    count in one hold of the lock.
  - Safe: after `pm_runtime_disable()`, while nothing calls
    `__pm_runtime_set_status()`, as `pm_runtime_force_suspend()` does with
    `pm_runtime_status_suspended()`; `rpm_resume()` and
    `rpm_check_suspend_allowed()` return on `disable_depth` above 0 before
    any status write.
- **Potentially unsafe usage**: writing `power.disable_depth` directly.
  - Unsafe: without `power.lock` on a device other tasks can reach, or as the
    0 -> 1 step while `runtime_error` is clear; at depth 0 -> 1
    `__pm_runtime_disable()` runs `__pm_runtime_barrier()` and sets
    `last_status`, which a direct write skips.
  - Safe: `pm_runtime_disable()` and `pm_runtime_enable()` instead.
  - Safe: under `power.lock` when the depth is already non-zero or
    `runtime_error` is set, undone by `pm_runtime_enable()`, as
    `__pm_runtime_set_status()` does; with `runtime_error` set `rpm_resume()`
    and `rpm_check_suspend_allowed()` return `-EINVAL` first.
  - Safe: the plain store in `pm_runtime_init()`, which `device_initialize()`
    reaches through `device_pm_init()` before the device is registered.

**Parents and children**

- `rpm_resume()` of a child: resumes the parent with `rpm_resume(parent, 0)`,
  which is synchronous; `RPM_ASYNC` is not passed on.
- Child status while the parent resumes: still `RPM_SUSPENDED`, with the
  child's `power.lock` dropped; `RPM_RESUMING` is set only afterwards.
- `rpm_resume()` returns `-EBUSY` when the parent is not `RPM_ACTIVE` after
  that call; this is the one error value that comes from the parent.
- On that `-EBUSY`: the parent's own error code is dropped, and the child's
  `runtime_status` and `runtime_error` are unchanged.
- `-EBUSY` from `rpm_resume()` can also be the return value of the child's
  `->runtime_resume()` callback, which `rpm_callback()` passes through.
- `rpm_suspend()`: no return value depends on the parent; its `-EBUSY` from
  `rpm_check_suspend_allowed()` is about the device's own `child_count`.
- No `-EAGAIN` and no `-EINVAL` comes from the parent's state.
- Parent with `disable_depth` non-zero: not resumed and its status not
  tested; the child's resume goes on whatever the parent's status is.
- `RPM_ASYNC` resume of a suspended child: queues the request and returns 0
  without resuming the parent, unless the `no_callbacks` shortcut applies.
- `no_callbacks` shortcut in `rpm_resume()`: applies when the parent is
  disabled, has `ignore_children` set or is `RPM_ACTIVE`; it runs before the
  `RPM_ASYNC` test, so `pm_request_resume()` makes such a child `RPM_ACTIVE`
  at once and returns 1.

**Calling context**

- `__pm_runtime_resume()`: its `might_sleep_if()` has a third condition,
  `dev->power.runtime_status != RPM_ACTIVE`; the other two functions test
  only `RPM_ASYNC` and `power.irq_safe`.
- Synchronous resume of a device that is `RPM_ACTIVE`: passes the check, and
  `rpm_resume()` returns 1 without dropping `power.lock`.
- That status read is made without the lock and before `usage_count` is
  incremented; it holds only if the caller already keeps the device active.
- `__pm_runtime_idle()` and `__pm_runtime_suspend()` with `RPM_GET_PUT`:
  return 0 before the `might_sleep_if()` when the count stays above zero, so
  the check fires only on the call that drops the last count.
- With `irq_safe`: `__rpm_callback()` and `rpm_idle()` do drop `power.lock`
  around the callback, with `spin_unlock()`; only interrupts stay disabled.
- The kerneldoc of `pm_runtime_irq_safe()` says the callbacks run "with the
  spinlock held"; the code does not do that.
- `pm_runtime_irq_safe()`: raises the parent's `usage_count` with
  `pm_runtime_get_sync()`, not `child_count`, and ignores the return value.
- `pm_runtime_irq_safe()`: does not test whether the parent is `irq_safe`
  and prints no warning.
- `pm_runtime_irq_safe()` itself: needs process context with interrupts on;
  it calls `pm_runtime_get_sync()` on the parent and uses `spin_lock_irq()`.

**Changing the runtime PM core**

- `rpm_idle()`: does not wait for a running idle notification; with
  `idle_notification` set it returns `-EINPROGRESS`.
- Waiter for `idle_notification`: only `__pm_runtime_barrier()`.
- `rpm_suspend()`: waits only for `RPM_SUSPENDING`; a synchronous call in
  `RPM_RESUMING` returns `-EAGAIN`.
- `no_callbacks` device: `rpm_suspend()` and `rpm_resume()` set the settled
  status directly; `RPM_SUSPENDING` and `RPM_RESUMING` are never visible.
- `power.lock` is also dropped in settled states: in `rpm_resume()` while the
  parent resumes (child `RPM_SUSPENDED`) and for `pm_runtime_put()` on the
  parent; in `rpm_suspend()` after `RPM_SUSPENDED` for the parent and
  suppliers.
- Test: `drivers/base/power/runtime-test.c`, built with
  `CONFIG_PM_RUNTIME_KUNIT_TEST`, suite `pm_runtime_test_cases`.
- The test calls the wrappers in `include/linux/pm_runtime.h` on a device
  from `kunit_device_register()`, which has no runtime PM callbacks.
- Return values the test expects: 0, 1, `-EAGAIN`, `-EACCES` and `-EINVAL`.
- Not covered by the test: `-EBUSY`, `-EINPROGRESS`, callback errors,
  `irq_safe`, and concurrent callers.

## Runtime PM during system sleep

**Runtime PM in each phase**

- `device_suspend_late()` in `drivers/base/power/main.c`: disables with
  `pm_runtime_disable()`, which passes `check_resume` true to
  `__pm_runtime_disable()`; it does not pass false.
- Resume request pending at that disable: carried out synchronously by
  `rpm_resume()` before runtime PM is disabled; it is not cancelled or lost.
- Pending idle, suspend or autosuspend request at that disable: cancelled by
  `__pm_runtime_barrier()`.
- `device_suspend()`: calls `pm_runtime_barrier()` before the callback, which
  also runs a pending resume request synchronously.
- `power.direct_complete` device: when the status is `RPM_SUSPENDED`,
  `device_suspend()` calls `pm_runtime_disable()` and, if the status is still
  `RPM_SUSPENDED`, the later suspend and resume phases run no callback;
  `device_resume()` does the matching `pm_runtime_enable()`.
- `pm_runtime_get_sync()` in a late, noirq or early callback, with
  `power.runtime_error` clear: returns 1 with no callback run when
  `power.runtime_status` and `power.last_status` are both `RPM_ACTIVE`, that
  is when the device was active at the disable and its status has not been
  changed since; otherwise `-EACCES`.
- Usage count on that `-EACCES`: already incremented by
  `__pm_runtime_resume()`; `pm_runtime_resume_and_get()` drops it again,
  `pm_runtime_get_sync()` does not.

**The PM work queue**

- There is no pm_start_workqueue() here; `pm_start_workqueues()` in
  `kernel/power/main.c` allocates `pm_wq`.
- Allocation: `alloc_workqueue("pm", WQ_UNBOUND, 0)`; it does not pass
  `WQ_FREEZABLE`, so `pm_wq` is not frozen during system suspend.
- Async resume request while tasks are frozen and runtime PM is still enabled
  for the device: `pm_runtime_work()` runs it without waiting for thaw.
- Async resume request after the disable in `device_suspend_late()`:
  `rpm_resume()` returns before it queues anything, for example with
  `-EACCES` or 1.
- Resume request still queued when the PM core reaches the device: run
  synchronously by `pm_runtime_barrier()` or `pm_runtime_disable()`, as
  "Runtime PM in each phase" says.
- Comment in `drivers/pci/pcie/pme.c` that calls `pm_wq` freezable: does not
  match the allocation.
- There is no pm_queue_pm_work() here; the helper is `queue_pm_work()` in
  `include/linux/pm_runtime.h`.

**Devices never enabled for runtime PM**

- `pm_runtime_block_if_disabled()`: returns true for every device whose
  runtime PM is disabled; it sets `power.last_status` to `RPM_BLOCKED` only if
  that field is still `RPM_INVALID`.
- `__pm_runtime_disable()`: stores the real status in `power.last_status` when
  it disables an enabled device, so that device is not blocked; a device that
  was never enabled has `RPM_INVALID` there until it is blocked.
- `device_prepare_smart_suspend()`: a parent or supplier for which
  `pm_runtime_blocked()` is true does not prevent smart suspend of the child
  or consumer.
- `pm_runtime_enable()` on a blocked device: prints "Attempt to enable runtime
  PM when it is blocked", calls `dump_stack()`, then enables as usual and sets
  `power.last_status` to `RPM_INVALID`; nothing is refused.
- That warning is tested only when `power.disable_depth` reaches 0.
- `device_prepare()` when `->prepare()` returns a negative value: calls
  `pm_runtime_unblock()` and `pm_runtime_put()` itself; `dpm_prepare()` does
  not put the device on `dpm_prepared_list`.

**Force suspend and force resume**

| Function | Skips the callback when |
|---|---|
| `pm_runtime_force_suspend()` | status is `RPM_SUSPENDED`, or `power.needs_force_resume` is already set |
| `pm_runtime_force_resume()` | `power.needs_force_resume` is clear and (`dev_pm_smart_suspend()` is false or status is `RPM_SUSPENDED`) |

- `pm_runtime_force_resume()`: makes no test of whether runtime PM is enabled,
  and does not set the status on success.
- `pm_runtime_force_suspend()`: tests `power.runtime_status`, not the
  hardware; a powered device still at the `RPM_SUSPENDED` that
  `pm_runtime_init()` sets gets no callback.
- Configuration: `pm_runtime_force_suspend()` is built with `CONFIG_PM`, and
  its stub returns 0; `pm_runtime_force_resume()` needs `CONFIG_PM_SLEEP`, and
  its stub returns `-ENXIO`.
- Outside system sleep: `pm_runtime_force_suspend()` is also called from
  remove callbacks, for example `sdhci_omap_remove()`; `pm_runtime_reinit()`
  clears `power.needs_force_resume` for that case.
- **Unsafe usage**: a system suspend callback that returns 0 after
  `pm_runtime_force_suspend()` when nothing in the resume path re-enables
  runtime PM; it stays disabled.
  - Safe: `pm_runtime_force_resume()` as the resume callback of the same
    phase, as `DEFINE_RUNTIME_DEV_PM_OPS()` does; it ends with
    `pm_runtime_enable()` on every path.
  - Safe: no undo when `pm_runtime_force_suspend()` itself returns an error;
    it has already called `pm_runtime_enable()`.
- **Potentially unsafe usage**: a suspend callback that returns an error after
  `pm_runtime_force_suspend()` succeeded.
  - Unsafe: when it returns without undoing; the PM core runs no resume
    callback of that phase for the device (`power.is_suspended`,
    `power.is_late_suspended` or `power.is_noirq_suspended` stays clear), so
    runtime PM stays disabled.
  - Safe: call `pm_runtime_force_resume()` before returning the error, as
    `renesas_sdhi_suspend()` does.
- **Potentially unsafe usage**: register access in the resume callback right
  after `pm_runtime_force_resume()` returns 0.
  - Unsafe: when the status was already `RPM_SUSPENDED` at force suspend, or
    `pm_runtime_need_not_resume()` was true there, that is usage count at
    most 1 and no counted active children; `power.needs_force_resume` is
    clear, the callback is skipped as the table says and the device stays
    `RPM_SUSPENDED`.
  - Safe: when the driver resumes the device and holds its own usage
    reference across the pair, as `sdhci_esdhc_suspend()` takes with
    `pm_runtime_resume_and_get()` and `sdhci_esdhc_resume()` drops;
    `pm_runtime_need_not_resume()` is then false.

**Flags behind force resume**

- `power.needs_force_resume`: set by `pm_runtime_force_suspend()` only when
  the callback succeeded and `pm_runtime_need_not_resume()` is false; a
  callback that ran for an unused device leaves it clear.
- Status while `power.needs_force_resume` is set: left untouched, so
  `RPM_ACTIVE` although the callback has suspended the hardware.
- Status when the callback succeeded and the flag stays clear:
  `pm_runtime_force_suspend()` calls `pm_runtime_set_suspended()`.
- `pm_runtime_force_suspend()` with the flag already set: returns 0 right
  after `pm_runtime_disable()` and runs no callback; the disable depth still
  goes up.
- `pm_runtime_force_resume()`: clears the flag and `power.smart_suspend` on
  every path, including a callback error.
- There is no pm_runtime_set_strict_midlayer() here; the accessors are
  `dev_pm_set_strict_midlayer()` and `dev_pm_strict_midlayer_is_set()` in
  `include/linux/device.h`.
- `power.strict_midlayer` effect: `get_callback()` in
  `drivers/base/power/runtime.c` returns only the callback from
  `dev->driver->pm`; there is no other test of middle-layer state.
- `power.strict_midlayer` is set in `pci_pm_prepare()` and
  `acpi_subsys_prepare()`, and cleared in `pci_pm_complete()` and
  `acpi_subsys_complete()`; `pci_pm_init()` does not set it.
- Flag clear, as it is for a device that reached neither prepare function
  and after `pci_pm_complete()` or `acpi_subsys_complete()`:
  `pm_runtime_force_suspend()` from a remove callback uses the normal lookup,
  middle layer first.
- Without `CONFIG_PM_SLEEP`: `dev_pm_set_strict_midlayer()` does nothing and
  `dev_pm_strict_midlayer_is_set()` returns false.

## Device callbacks

**Defining a dev_pm_ops**

- "Deprecated" in `include/linux/pm.h`: only two macros carry the word.

| Marked deprecated | Named in its place | Defined in |
|---|---|---|
| `SIMPLE_DEV_PM_OPS()` | `DEFINE_SIMPLE_DEV_PM_OPS()` | `include/linux/pm.h` |
| `UNIVERSAL_DEV_PM_OPS()` | `DEFINE_RUNTIME_DEV_PM_OPS()` | `include/linux/pm_runtime.h` |

- `SET_SYSTEM_SLEEP_PM_OPS()`, `SET_LATE_SYSTEM_SLEEP_PM_OPS()`,
  `SET_NOIRQ_SYSTEM_SLEEP_PM_OPS()`, `SET_RUNTIME_PM_OPS()`: no deprecation
  comment and no named replacement in `include/linux/pm.h`.
- Those four macros: each expands to the macro of the same name without the
  `SET_` prefix under `CONFIG_PM_SLEEP` (`CONFIG_PM` for
  `SET_RUNTIME_PM_OPS()`), and to nothing otherwise.
- DEFINE_UNIVERSAL_DEV_PM_OPS(): not in this tree.
- `RUNTIME_PM_OPS()`: assigns `runtime_suspend`, `runtime_resume` and
  `runtime_idle` bare, with no `pm_ptr()`.
- Runtime callbacks set through `RUNTIME_PM_OPS()`: become unreferenced
  without `CONFIG_PM` when the struct is `static` and referenced only through
  `.pm = pm_ptr(&ops)`.
- `pm_ptr()` and `pm_sleep_ptr()`: `include/linux/pm.h` has no comment saying
  where each goes; the mechanism is described in the `PTR_IF()` kerneldoc in
  `include/linux/util_macros.h`.
- Exported structs: the symbol exists only under the option the export macro
  keys on; otherwise `_DISCARD_PM_OPS()` emits a static `__static_##name`.

| Export family | Symbol defined under | Wrapper for `.pm` |
|---|---|---|
| `EXPORT_DEV_SLEEP_PM_OPS()`, `EXPORT_SIMPLE_DEV_PM_OPS()` and their GPL and NS forms, for example `EXPORT_NS_GPL_SIMPLE_DEV_PM_OPS()` | `CONFIG_PM_SLEEP` | `pm_sleep_ptr()` |
| `EXPORT_DEV_PM_OPS()`, `EXPORT_RUNTIME_DEV_PM_OPS()` and their GPL and NS forms, for example `EXPORT_NS_GPL_RUNTIME_DEV_PM_OPS()` | `CONFIG_PM` | `pm_ptr()` |

- `pm_ptr()` around a struct from the `CONFIG_PM_SLEEP` family: with
  `CONFIG_PM=y` and `CONFIG_PM_SLEEP=n` the reference survives and the symbol
  has no definition.

**Callback selection**

- `__rpm_get_callback()`: falls back to `__rpm_get_driver_callback()` whenever
  the member read from the selected ops is NULL, not only when no ops was
  selected.
- `device_suspend()`: the pm_domain, type and class branches all `goto Run`,
  where a NULL `callback` is replaced by `pm_op(dev->driver->pm, state)`.
- `device_suspend()`: the legacy bus branch is the only one that skips the
  driver lookup.
- Legacy bus `suspend`: tested before the driver, not after; when
  it is taken, `dev->driver->pm` is not consulted even if set.
- legacy_resume(): not in this tree; `device_resume()` puts
  `dev->bus->resume` in `callback` and runs it through `dpm_run_callback()`.
- Legacy bus `resume` in `device_resume()`: chosen without `pm_op()`, so it
  runs for every `state.event`.
- `struct class` and `struct device_type`: have a `pm` pointer only, no legacy
  `suspend` or `resume`; the "bus or class" in the `legacy_suspend()` kerneldoc
  has no class caller.
- `suspend` and `resume` in `struct device_driver`: `drivers/base/power/` never
  calls them; `device_pm_check_callbacks()` only tests them for
  `power.no_pm_callbacks`.
- NULL `runtime_idle` in `rpm_idle()`: treated as success, and `rpm_idle()`
  goes on to `rpm_suspend()` with `RPM_AUTO`.
- `pm_runtime_force_suspend()` and `pm_runtime_force_resume()`: look up through
  `get_callback()`, not `RPM_GET_CALLBACK()`.

## Device phases of system sleep

**Driver flags**

- Clearing: `device_unbind_cleanup()` in `drivers/base/dd.c` calls
  `dev_pm_set_driver_flags(dev, 0)`; it runs on unbind and on probe failure,
  so a driver need not clear the flags itself.

| Flag | Tested by | Easy to miss |
|---|---|---|
| `DPM_FLAG_NO_DIRECT_COMPLETE` | `device_prepare()` | — |
| `DPM_FLAG_SMART_PREPARE` | `pci_pm_prepare()`, `acpi_subsys_prepare()` only | the PM core never tests it |
| `DPM_FLAG_SMART_SUSPEND` | `device_prepare_smart_suspend()` only | all other code reads `dev_pm_smart_suspend()` |
| `DPM_FLAG_MAY_SKIP_RESUME` | `device_suspend()`, `device_suspend_noirq()` | covers noirq and early resume only |

- `DPM_FLAG_SMART_PREPARE`: the only effect is that a driver `->prepare()`
  returning 0 makes the bus type return 0.
- `DPM_FLAG_SMART_PREPARE` with a positive driver return: the value is not
  passed through; `pci_pm_prepare()` still applies `pci_dev_need_resume()`
  and `acpi_subsys_prepare()` still applies `acpi_dev_needs_resume()`.
- `DPM_FLAG_SMART_SUSPEND`: `device_prepare_smart_suspend()` treats a device
  with `power.no_pm_callbacks` as if the flag were set, and has no wakeup
  test.
- `DPM_FLAG_MAY_SKIP_RESUME`: `device_resume()` makes no skip test, and
  `pci_pm_resume()` does not call `dev_pm_skip_resume()`, so the driver's
  `->resume()` runs even when its noirq and early resume were skipped.

**Direct complete**

- `device_prepare()`: sets `power.direct_complete` from the event, the
  `->prepare()` return value or `power.no_pm_callbacks`, and
  `DPM_FLAG_NO_DIRECT_COMPLETE` only; the runtime PM status and
  `pm_runtime_enabled()` play no part in it.
- Runtime status: tested in `device_suspend()` with
  `pm_runtime_status_suspended()`, which ignores the disable depth, so a
  device with runtime PM disabled and status `RPM_SUSPENDED` qualifies.
- There is no __device_suspend() here; `device_suspend()` does that job.
- `device_suspend()` also clears the flag when `device_may_wakeup()` or
  `device_wakeup_path()` is true.
- Parent and suppliers: cleared only by
  `dpm_clear_superiors_direct_complete()`, called from the child's
  `device_suspend()` after its callback returned 0 or it had none;
  `device_prepare()` and `dpm_prepare()` clear nothing in the parent.
- `dpm_clear_superiors_direct_complete()`: clears every supplier, without
  looking at link flags or link status.
- `dpm_clear_superiors_direct_complete()` is not called for a child that
  direct-completes itself, is `power.syscore`, or left early on
  `async_error` or a pending wakeup.
- Late and early phases: `device_suspend_late()` and `device_resume_early()`
  test `power.direct_complete` alone and leave before touching runtime PM;
  only the two noirq functions test `power.syscore || power.direct_complete`.
- `device_resume()`: reaches its direct-complete branch only when
  `power.is_suspended` is set, and does not wait for the parent or suppliers
  there.

**Smart suspend and skipped resume**

- `power.smart_suspend`: stored as false by `device_prepare()` for every
  device whose runtime PM is disabled when it runs;
  `pm_runtime_block_if_disabled()` returns true and
  `device_prepare_smart_suspend()` is not called. `device_prepare()` stores
  nothing when it returns early for `power.syscore` or for a negative
  `->prepare()` value.
- `pm_runtime_force_resume()` clears `power.smart_suspend`, so
  `dev_pm_skip_suspend()` returns false for that device afterwards.
- Core tests: `device_suspend_late()`, `device_suspend_noirq()`,
  `device_resume_noirq()` and `device_resume_early()` skip the driver
  callback on the helpers only when the device has no `pm_domain`, `type`,
  `class` or `bus` callback for that phase; a middle layer with a callback
  must test them itself.
- `dev_pm_skip_resume()` on `PM_EVENT_THAW`: returns
  `dev_pm_skip_suspend(dev)`, not `power.must_resume`.
- `dev_pm_skip_resume()` on any event other than `PM_EVENT_RESTORE` and
  `PM_EVENT_THAW`: returns `!power.must_resume`; that includes
  `PM_EVENT_RECOVER`.
- `power.must_resume` in `device_suspend_noirq()`: set when
  `DPM_FLAG_MAY_SKIP_RESUME` is clear, or `power.may_skip_resume` is clear,
  or `pm_runtime_need_not_resume()` is false.
- `pm_runtime_need_not_resume()`: false when the usage count is above 1, or
  when `power.child_count` is nonzero and `power.ignore_children` is clear.
- Wakeup: the core has no wakeup test for `power.must_resume`;
  `pci_pm_suspend_noirq()` and `acpi_subsys_suspend_noirq()` clear
  `power.may_skip_resume` for a device that can wake up but is not enabled
  to, as their last step, so not after an earlier return such as the one on
  `dev_pm_skip_suspend()`.
- `dpm_superior_set_must_resume()`: sets `power.must_resume` in the parent
  and in every supplier, with no test of link flags or status;
  `device_prepare_smart_suspend()` looks at `DL_FLAG_PM_RUNTIME` links only.
- `device_resume_noirq()` when the resume is skipped: calls
  `pm_runtime_set_suspended()`.
- `device_resume_noirq()` when the resume is not skipped: calls
  `pm_runtime_set_active()` if `dev_pm_smart_suspend()` is true; there is no
  set_active field in `struct dev_pm_info`.
- Both status calls: made before the callback lookup, so also when a
  middle-layer callback runs; their return values are ignored.
- No status change: for a device that leaves `device_resume_noirq()` early
  (`power.syscore`, `power.direct_complete`, `power.is_noirq_suspended`
  clear, or `dpm_wait_for_superior()` false).
- Aborted noirq suspend: for a device with `power.is_noirq_suspended` clear
  and `dev_pm_skip_suspend()` true, `device_resume_noirq()` clears
  `power.must_resume`, so `dev_pm_skip_resume()` is true in the early phase
  unless the event is `PM_EVENT_RESTORE`.

**Asynchronous suspend and resume**

- `dpm_wait()`: waits when the caller is async, or when `pm_async_enabled`
  is set and the target has `power.async_suspend`; it returns at once for a
  target with `power.no_pm`.
- `dpm_wait()` does not test `pm_trace_is_enabled()`; `is_async()` does.
- Links skipped by `dpm_wait_for_suppliers()` and `dpm_wait_for_consumers()`:
  `DL_STATE_DORMANT` links and links for which
  `device_link_flag_is_sync_state_only()` is true.
- `is_async()`: has no test for PM callbacks; a device without callbacks is
  async if the three conditions hold.
- `__dpm_async()`: calls `async_schedule_dev_nocall()`, not
  `async_schedule_dev()`; when it returns false the reference is dropped,
  and when that happens under `dpm_async_fn()` the list walk handles the
  device synchronously.
- Start of async work, in each of the six phases:
  1. the first walk starts async work only for `dpm_leaf_device()` devices
     (suspend) or `dpm_root_device()` devices (resume);
  2. a finished device starts its parent and suppliers through
     `dpm_async_suspend_superior()`, or its children and consumers through
     `dpm_async_resume_subordinate()`;
  3. the main walk calls `dpm_async_fn()` for every device; it does nothing
     more when `power.work_in_progress` is already set.
- `dpm_async_suspend_superior()`: not called when the device failed or
  `async_error` is set.
- `async_wip_mtx`: guards `power.work_in_progress`; see `dpm_async_fn()` and
  `dpm_async_with_cleanup()`. `dpm_clear_async_state()` resets the field
  under `dpm_list_mtx` instead.
- Phase barrier: each of the six phases ends with `async_synchronize_full()`;
  that is the only order between unrelated async devices.
- `dpm_prepare()` and `dpm_complete()`: never asynchronous; `dpm_list` order
  for prepare, reverse order for complete.
- `device_pm_wait_for_dev()`: the exported way for a driver to wait for a
  device it has no parent or link relation to; it returns `async_error`.

**Failure and rollback**

- `resume_event()`:

| Suspend event | Message returned |
|---|---|
| `PM_EVENT_SUSPEND` | `PMSG_RESUME` |
| `PM_EVENT_FREEZE`, `PM_EVENT_QUIESCE` | `PMSG_RECOVER` |
| `PM_EVENT_HIBERNATE` | `PMSG_RESTORE` |
| any other, for example `PM_EVENT_POWEROFF` | `PMSG_ON` |

- `PMSG_ON`: `pm_op()`, `pm_late_early_op()` and `pm_noirq_op()` return NULL
  for it, so the noirq and early rollback runs no callback; the flags are
  still cleared and runtime PM is re-enabled.
- Who rolls back:

| Failing function | Rolls back itself | Left to the caller |
|---|---|---|
| `dpm_suspend_noirq()` | `dpm_resume_noirq(resume_event(state))` | early resume and later |
| `dpm_suspend_late()` | `dpm_resume_early(resume_event(state))` | `dpm_resume_end()` |
| `dpm_suspend_end()` | as above, plus `dpm_resume_early()` after a noirq failure | `dpm_resume_end()` |
| `dpm_suspend()`, `dpm_prepare()` | nothing | everything |

- Caller's message for `dpm_resume_end()`: `PMSG_RESUME` in
  `suspend_devices_and_enter()`, `PMSG_RECOVER` in `hibernation_restore()`,
  `PMSG_RESTORE` in `hibernation_platform_enter()`.
- Devices walked: every device of the phase, since the suspend loop splices
  the devices it did not reach onto the target list.
- Devices resumed: only those whose flag for the phase is set; the failing
  device's flag stays clear, so its resume callback for that phase is not
  called.
- `-EAGAIN` from prepare: `dpm_prepare()` clears the error but leaves the
  device at the head of `dpm_list`, so the next iteration calls
  `device_prepare()` on the same device again.

**Pending wakeup events**

- Phases that check: `device_suspend()` and `device_suspend_late()` call
  `pm_wakeup_pending()`; `device_suspend_noirq()`, `device_prepare()` and
  `dpm_prepare()` do not.
- After the noirq phase: `syscore_suspend()` checks before its callbacks and
  returns `-EBUSY`; `suspend_enter()` checks again after it;
  `s2idle_enter()` checks under `s2idle_lock` each time `s2idle_loop()`
  calls it.
- `device_suspend()`: calls `pm_runtime_barrier()`, which returns void, and
  then `pm_wakeup_pending()`; it does not call `pm_wakeup_event()`.
- `device_suspend_late()`: checks before its `pm_runtime_disable()`, so an
  aborted device keeps runtime PM enabled and `power.is_late_suspended`
  clear.
- On a hit: `async_error` is set to `-EBUSY` and the local `error` stays 0;
  no device name goes to `dpm_save_failed_dev()`, but the phase still calls
  `dpm_save_failed_step()`.
- `pm_wakeup_pending()`: a hit on the event counters clears
  `events_check_enabled`, so a later call returns false unless
  `pm_abort_suspend` is positive.
- **Unsafe usage**: calling `pm_wakeup_pending()` again to learn whether the
  phase was aborted.
  - Safe: read `async_error`, as `device_suspend_late()` does before its own
    `pm_wakeup_pending()` call.

**Changing the device phases**

- `device_pm_sleep_init()`: initialises `power.completion` and calls
  `complete()` on it at once; `device_pm_init()` only calls it.
- `dpm_clear_async_state()`: reinitialises the completion in the first walk
  of each phase, under `dpm_list_mtx`, in the same walk that starts async
  work for leaf or root devices.
- Continuations: `dpm_async_resume_children()` and
  `dpm_async_suspend_parent()` take `dpm_list_mtx` before they start a
  related device, which keeps them out until that walk has ended.
- **Unsafe usage**: an exit from a `device_suspend()` or `device_resume()`
  family function that does not reach `complete_all()` on
  `power.completion`; `dpm_wait()` waits with no timeout.
  - Safe: jump to the function's `Complete` or `Out` label, as the
    `async_error` exit of `device_suspend_noirq()` does.
- **Unsafe usage**: leaving a suspend loop on error without completing the
  devices it did not reach; async work already running may wait on them.
  - Safe: call `dpm_async_suspend_complete_all()` on the source list before
    `list_splice_init()`, as `dpm_suspend()` does.
- **Unsafe usage**: leaving `device_suspend_late()` after its
  `pm_runtime_disable()` with `power.is_late_suspended` clear and runtime PM
  still disabled; `device_resume_early()` re-enables only when the flag is
  set.
  - Safe: call `pm_runtime_enable()` first, as the callback error path of
    `device_suspend_late()` does.
  - Safe: leave before `pm_runtime_disable()`, as the `async_error` and
    `pm_wakeup_pending()` exits do.
- Flags set without a callback success: `power.is_suspended` on the
  direct-complete path of `device_suspend()`; `power.is_late_suspended` and
  `power.is_noirq_suspended` at the `Skip` label.
- `power.is_prepared`: `dpm_complete()` clears it without testing it and
  calls `device_complete()` for every device on `dpm_prepared_list`;
  `device_resume()` clears it before the resume callback.
- List on failure: each suspend loop moves a device to the target list
  before handling it, so the failing device is on the target list with its
  flag clear; the devices not reached are spliced onto the same list.
- `dpm_prepare()` failure: the failing device stays on `dpm_list` without
  `power.is_prepared` and gets no `->complete()`; `device_prepare()` has
  already dropped its runtime PM reference.

## System-wide transitions and hibernation

**System state during device callbacks**

- Task freezing: happens only with `CONFIG_SUSPEND_FREEZER`; without it
  `suspend_freeze_processes()` in `kernel/power/power.h` returns 0 and no
  task is frozen when the device callbacks run.
- Filesystem freeze: `suspend_prepare()` calls `filesystems_freeze()`
  unconditionally, before freezing tasks; `filesystem_freeze_enabled` is
  only its argument.
- `filesystem_freeze_enabled` false (the default): superblocks whose type
  sets `FS_POWER_FREEZE` are still frozen; `fs/efivarfs/super.c` sets it.
- `filesystem_freeze_enabled` true: every superblock with a `freeze_fs` or
  `freeze_super` operation is frozen; see `filesystems_freeze_callback()`
  in `fs/super.c`.
- Filesystem sync: `enter_state()` calls `pm_sleep_fs_sync()` in
  `kernel/power/main.c` only when `sync_on_suspend_enabled` is set; there
  is no sync_filesystems() function.
- `pm_sleep_fs_sync()`: runs `ksys_sync_helper()` from a work item and
  returns `-EBUSY` once `pm_wakeup_pending()` is true, which aborts the
  suspend before `suspend_prepare()`.
- Aborted sync: the work item is not cancelled, so `ksys_sync()` keeps
  running after `enter_state()` has returned.
- Signals: do not interrupt the sync; the wait is `wait_event_timeout()`.
- Console: there is no suspend_console(); `console_suspend_all()` in
  `kernel/printk/printk.c` marks consoles `CON_SUSPENDED` only when
  `console_suspend_enabled` is set.
- Driver probing: blocked from `dpm_prepare()` (`device_block_probing()`)
  until `dpm_complete()`.
- GFP mask: `pm_restrict_gfp_mask()` runs in `dpm_suspend_start()` after
  `dpm_prepare()`, so `->prepare` runs with `__GFP_IO` and `__GFP_FS`
  still allowed and `->suspend` without them.
- Late phase: `device_suspend_late()` calls `pm_runtime_disable()` for one
  device just before that device's callback; devices not yet processed,
  such as its parent, still have runtime PM enabled.
- Noirq phase: `suspend_device_irqs()` leaves enabled, besides armed wakeup
  interrupts, lines with an `IRQF_NO_SUSPEND` action, chained descriptors
  and nested-thread interrupts; see `suspend_device_irq()` in
  `kernel/irq/pm.c`.
- After noirq: `suspend_enter()` calls `pm_sleep_disable_secondary_cpus()`,
  not `suspend_disable_secondary_cpus()` directly; the wrapper calls
  `cpuidle_pause()` first.

**System-wide locks**

- `lock_system_sleep()` return value: the whole of `current->flags` from
  before the call, not a boolean; `unlock_system_sleep()` tests
  `PF_NOFREEZE` in it.
- `system_transition_mutex` and the `reboot` syscall: the syscall in
  `kernel/reboot.c` holds it with plain `mutex_lock()` while it runs the
  command, so restart, power-off and `kernel_kexec()` are excluded too.
- Takers that fail with `-EBUSY` instead of waiting: `enter_state()`,
  `snapshot_ioctl()` and `hibernate_compressor_param_set()` use
  `mutex_trylock()`.
- `software_resume()`: takes `system_transition_mutex` with plain
  `mutex_lock()`, without setting `PF_NOFREEZE`.
- `hibernate_acquire()` in `kernel/power/hibernate.c`: every caller, for
  example `hibernate()` and `snapshot_open()`, calls it with
  `system_transition_mutex` already held.
- `hibernate_acquire()` versus the mutex: `/dev/snapshot` keeps the claim
  from `snapshot_open()` to `snapshot_release()`, while
  `system_transition_mutex` is dropped between the file operations.
- `device_pm_lock()`: the wrapper for code outside
  `drivers/base/power/main.c`, for example `device_move()` and
  `device_pm_move_to_tail()` in `drivers/base/core.c`; `device_pm_add()`,
  `device_pm_remove()` and the `dpm_*` phase functions take `dpm_list_mtx`
  directly.
- `dpm_suspend_start()` and `dpm_resume_end()`: call
  `pm_restrict_gfp_mask()` and `pm_restore_gfp_mask()`, which warn unless
  `system_transition_mutex` is locked; a caller outside `kernel/power/`
  needs it held, and `do_suspend()` in `drivers/xen/manage.c` takes it
  first.

**Hibernation sequence**

- Success path: models have the five stages, messages and callbacks right;
  see `hibernation_snapshot()`, `create_image()`,
  `hibernation_platform_enter()` and `hibernation_restore()` in
  `kernel/power/hibernate.c`.
- Message after a failure in the hibernating kernel: chosen by
  `in_suspend ? (error ? PMSG_RECOVER : PMSG_THAW) : PMSG_RESTORE`;
  `in_suspend` is set to 1 only just before `swsusp_arch_suspend()`, so
  with `in_suspend` 0 on entry earlier failures give `PMSG_RESTORE`, not
  `PMSG_RECOVER`.

| Failure point | What the core sends next |
|---|---|
| `dpm_prepare(PMSG_FREEZE)`, `hibernate_preallocate_memory()` or `freeze_kernel_threads()` | `dpm_complete(PMSG_RECOVER)` only: `->complete`, no thaw callback |
| `dpm_suspend(PMSG_FREEZE)` | `dpm_resume()` and `dpm_complete()` with `PMSG_RESTORE`: `->restore`, `->complete` |
| late or noirq freeze, inside `dpm_suspend_end(PMSG_FREEZE)` | the phase unwinds itself with `PMSG_RECOVER`, then `hibernation_snapshot()` sends `PMSG_RESTORE` |
| `platform_pre_snapshot()`, `pm_sleep_disable_secondary_cpus()`, `syscore_suspend()` or a pending wakeup in `create_image()` | `PMSG_RESTORE` for the noirq, early and main phases |
| `swsusp_arch_suspend()` returns an error | `PMSG_RECOVER` for all three phases |
| `swsusp_write()` | nothing; devices stay as the thaw left them |
| `hibernation_platform_enter()`, after `hibernation_ops->begin()` succeeded | `PMSG_RESTORE` |

- Late or noirq freeze failure: a driver can therefore see `->thaw_noirq`
  or `->thaw_early` followed by `->restore`.
- `power_down()` after `hibernation_platform_enter()` fails: `-EAGAIN` or
  `-EBUSY` rolls back and the system keeps running; any other error falls
  through to `kernel_power_off()` or `kernel_halt()`, so drivers then see
  `->shutdown`.
- `PMSG_HIBERNATE`: sent only by `hibernation_platform_enter()`, which
  `hibernate()` reaches only in `HIBERNATION_PLATFORM` mode;
  `hibernation_mode` starts as `HIBERNATION_SHUTDOWN` and becomes platform
  mode when `hibernation_set_ops()` installs ops, and `power_down()`
  switches to it after a failed `HIBERNATION_SUSPEND` when ops are
  installed.
- `HIBERNATION_TEST_RESUME` mode: no power-off; after the image is written
  `hibernate()` calls `load_image_and_restore()` in the same kernel, so
  drivers see `PMSG_QUIESCE` and then `PMSG_RESTORE`.
- `PMSG_POWEROFF`: defined in `include/linux/pm.h` and mapped to the
  poweroff callbacks by `pm_op()`, but nothing in this tree sends it.

**Situations a thaw callback sees**

| Situation | Thaw callbacks run | `pm_hibernate_is_recovering()` |
|---|---|---|
| image created by `hibernation_snapshot()` | `PMSG_THAW`: noirq, early, main | false |
| `swsusp_arch_suspend()` returned an error | `PMSG_RECOVER`: noirq, early, main | true |
| late or noirq phase of `PMSG_FREEZE` or `PMSG_QUIESCE` failed and unwinds | `PMSG_RECOVER`: `->thaw_early`, after `->thaw_noirq` when the noirq phase failed; the caller picks the message for the main phase | true |
| any other failure from `dpm_suspend(PMSG_FREEZE)` on, before `swsusp_arch_suspend()`, with `in_suspend` 0 on entry | none; `PMSG_RESTORE` runs `->restore` | false |
| boot kernel, `hibernation_restore()` failed | `PMSG_RECOVER`: main, after noirq and early if those phases were reached | true |
| `hibernate_quiet_exec()`, whatever `func` returns | `PMSG_THAW`: noirq, early, main | false |

- `hibernate_quiet_exec()`: the system keeps running after its `PMSG_THAW`;
  `drivers/nvdimm/core.c` calls it.
- Outside the hibernation core: `do_suspend()` in `drivers/xen/manage.c`
  sends `PMSG_THAW` when the suspend was cancelled, and the system keeps
  running.
- `pm_hibernate_is_recovering()`: defined in `drivers/base/power/main.c`;
  it reads `pm_transition`, which only the six suspend and resume phase
  functions write and nothing clears.
- In `->prepare`, and in `->complete` when the caller goes straight to
  `dpm_complete()` after a failed `dpm_prepare()`, as
  `hibernation_snapshot()` does, `pm_hibernate_is_recovering()` reports the
  last phase of an earlier transition.
- `swsusp_write()` failure after a normal thaw: `hibernate()` sends no
  further device message; only the `PM_POST_HIBERNATION` notifier follows.
- **Potentially unsafe usage**: a `->thaw` that returns 0 without resuming
  the hardware.
  - Unsafe: when the system keeps running after the thaw, because nothing
    later resumes the device: `PMSG_RECOVER`, `PMSG_THAW` from
    `hibernate_quiet_exec()`, or `swsusp_write()` failing.
  - Unsafe: in `HIBERNATION_SUSPEND` mode, where `power_down()` calls
    `suspend_devices_and_enter()` and `->prepare` and `->suspend` run on
    the device next.
  - Unsafe: in `HIBERNATION_TEST_RESUME` mode unless `->freeze` accepts a
    device that is still frozen; `hibernation_restore()` sends
    `PMSG_QUIESCE` to the same kernel.
  - Unsafe: when `swsusp_write()` needs the device to reach the image.
  - Safe: when the message is `PMSG_THAW` from `hibernation_snapshot()`,
    `swsusp_write()` then succeeds, the mode is not suspend or
    test_resume, and the callbacks that run next accept a frozen device;
    `amdgpu_pmops_thaw()` in `drivers/gpu/drm/amd/amdgpu/amdgpu_drv.c`
    skips only when `pm_hibernate_is_recovering()` and
    `pm_hibernation_mode_is_suspend()` are both false.
  - Safe: the callbacks that follow return early for the frozen device, as
    `amdgpu_pmops_prepare()`, `amdgpu_pmops_poweroff()` and
    `amdgpu_pci_shutdown()` do on `adev->in_s4 && adev->in_suspend`;
    `amdgpu_device_pm_notifier()` sets `in_s4`.

## Wakeup

**Device wakeup capability**

- `device_may_wakeup()` without `CONFIG_PM_SLEEP`: tests
  `dev->power.should_wakeup`, not a wakeup source; `dev->power.wakeup` does not
  exist in `struct dev_pm_info` in that configuration, so code that reads the
  field directly instead of calling the helper does not build there.
- `device_wakeup_enable()` return values with `CONFIG_PM_SLEEP`: `-EINVAL` if
  `can_wakeup` is clear, `-ENOMEM` if `wakeup_source_register()` fails,
  `-EEXIST` from `device_wakeup_attach()` if a source is already attached.
- `device_wakeup_disable()`: returns `void`.
- `device_init_wakeup(dev, true)` on a device that already has wakeup enabled,
  with `CONFIG_PM_SLEEP`: returns `-EEXIST` and leaves the existing source
  attached. The i2c core, for example, enables wakeup for a client with
  `I2C_CLIENT_WAKE` before it calls the driver's probe; see
  `i2c_device_probe()` in `drivers/i2c/i2c-core-base.c`.
- Unbind without the undo: nothing in `drivers/base/dd.c` disables wakeup; the
  source stays attached until `device_del()` reaches `device_pm_remove()`,
  which calls `device_wakeup_disable()`, unless the bus remove callback
  disables it, as `i2c_device_remove()` does.
- Rebind after a missing undo: the next `device_init_wakeup(dev, true)` returns
  `-EEXIST`, so a probe that propagates the return value fails.
- `device_wakeup_disable()` with `can_wakeup` clear: returns without detaching
  anything. `device_init_wakeup(dev, false)` disables first and clears the
  capability second; the reverse order would leave the source attached.
- **Potentially unsafe usage**: `device_set_wakeup_capable(dev, false)` on its
  own as the removal undo.
  - Unsafe: while a wakeup source is attached, which user space can cause on
    a capable, registered device by writing "enabled" to `power/wakeup`
    (`wakeup_store()` in `drivers/base/power/sysfs.c`). While `can_wakeup`
    stays clear, every later `device_wakeup_disable()`, including the one in
    `device_pm_remove()`, returns early and the source is not unregistered.
  - Safe: after the source is detached, as `device_init_wakeup(dev, false)`
    does, or as `flexcan_remove()` does with
    `device_set_wakeup_enable(dev, false)` first.
- `devm_device_init_wakeup()`: exists under that name, static inline in
  `include/linux/pm_wakeup.h`, takes only `dev`.
- `devm_device_init_wakeup()` return value: that of
  `devm_add_action_or_reset()` only; the result of
  `device_init_wakeup(dev, true)` is discarded, so it returns 0 when the enable
  failed with `-EEXIST` or `-ENOMEM`.
- `device_init_wakeup(dev, false)` called twice (by hand in remove and again by
  the devres action): the second call is a no-op, since
  `device_wakeup_disable()` and `device_set_wakeup_capable()` both return early
  when `can_wakeup` is already clear.
- Wake IRQ: `device_init_wakeup(dev, false)` does not touch
  `dev->power.wakeirq`; undo `dev_pm_set_wake_irq()` or
  `dev_pm_set_dedicated_wake_irq()` separately with `dev_pm_clear_wake_irq()`,
  or use `devm_pm_set_wake_irq()` in `drivers/base/power/wakeirq.c` in place
  of `dev_pm_set_wake_irq()`; `dev_pm_set_dedicated_wake_irq()` has no managed
  form.

## Model gaps

### Other mistakes models make

- Models take `pm_runtime_reinit()` to zero `power.runtime_error`. It
  returns at once while runtime PM is enabled, and clears the field only
  through `pm_runtime_set_suspended()`, when the device is disabled and its
  status is `RPM_ACTIVE`. Besides `pm_runtime_init()`, only
  `__pm_runtime_set_status()` clears it.
- Models take `device_suspend_late()` to call
  `__pm_runtime_disable(dev, false)`, so that a pending resume request is
  dropped. `pm_runtime_remove()` is the only caller that passes false.
- Models take filesystems to be frozen for sleep only when
  `/sys/power/freeze_filesystems` is set. `hibernate()` calls
  `filesystems_freeze()` whatever `filesystem_freeze_enabled` is, as
  `suspend_prepare()` does; see "System state during device callbacks" for
  what is then frozen.
- Models take `RUNTIME_PM_OPS()` to wrap its members in `pm_ptr()`. In
  `include/linux/pm.h` only `SYSTEM_SLEEP_PM_OPS()`,
  `LATE_SYSTEM_SLEEP_PM_OPS()` and `NOIRQ_SYSTEM_SLEEP_PM_OPS()` wrap their
  members, with `pm_sleep_ptr()`.
- Models take `pm_wakeup_clear()` to take no argument and to run in
  `suspend_prepare()`. It takes an IRQ number and resets `pm_abort_suspend`
  only for 0; `freeze_processes()` and `pm_sleep_fs_sync()` call it with 0.
- Models place `pm_restrict_gfp_mask()` in the suspend core. For its caller
  on the suspend path see "System-wide locks"; `pm_restrict_gfp_mask()` and
  `pm_restore_gfp_mask()` nest through `saved_gfp_count` in
  `kernel/power/main.c`.
