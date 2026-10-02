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
