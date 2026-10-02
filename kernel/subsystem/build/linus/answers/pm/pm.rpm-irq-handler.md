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
