- `drivers/base/regmap/regmap-irq.c` has no suspend or resume hook. Mask and
  wake registers are written only at registration and in
  `regmap_irq_sync_unlock()`; a parent whose device loses register state must
  restore them itself.
- `suspend_device_irqs()` and `resume_irqs()` in `kernel/irq/pm.c` skip
  nested-thread descriptors. Child interrupts are never disabled or armed by
  the core; only the primary is.
- `dpm_suspend_noirq()` calls `suspend_device_irqs()` before the noirq
  callbacks; `dpm_resume_noirq()` calls `resume_device_irqs()` after them.
- **Potentially unsafe usage**: leaving the primary interrupt enabled across
  the parent's suspend and resume callbacks.
  - Unsafe: when the bus controller suspends before `suspend_device_irqs()`
    or resumes after `resume_device_irqs()`. `regmap_irq_thread()` then fails
    in `read_irq_data()`, acks nothing, calls no child handler and returns
    `IRQ_NONE`. On an adapter marked by `i2c_mark_adapter_suspended()`,
    `__i2c_check_suspended()` returns `-ESHUTDOWN` and warns.
  - Safe: `disable_irq()` on the primary in the parent's suspend callback and
    `enable_irq()` in resume, as `max77686_suspend()` and `max77686_resume()`
    in `drivers/mfd/max77686.c` do; `regmap_irq_thread()` then cannot run
    while the bus is suspended.
  - Safe: when the bus controller suspends and resumes in its noirq
    callbacks, as `exynos5_i2c_suspend_noirq()` does, and the primary was
    requested without `IRQF_NO_SUSPEND`; the callbacks run inside the window
    set by `dpm_suspend_noirq()` and `dpm_resume_noirq()`, and
    `suspend_device_irq()` skips a descriptor with `no_suspend_depth`.
- Wake and masking: `regmap_irq_set_wake()` and the wake part of
  `regmap_irq_sync_unlock()` never change `mask_buf`. Child interrupts without
  wake stay unmasked in the chip during suspend.
- `wake_base` polarity: a 1 in the register means wake disabled; with
  `wake_invert` a 1 means wake enabled.
- Failure on the primary: `regmap_irq_sync_unlock()` drops the return value of
  `enable_irq_wake(d->irq)` and `regmap_irq_set_wake()` returns 0 always. The
  child's `enable_irq_wake()` succeeds even when `set_irq_wake_real()` returns
  `-ENXIO` for the primary's chip.
