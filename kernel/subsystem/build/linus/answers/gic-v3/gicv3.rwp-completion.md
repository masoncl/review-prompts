- `GICR_CTLR_RWP`: bit 3 of `GICR_CTLR`; `GICD_CTLR_RWP`: bit 31 of
  `GICD_CTLR`; both in `include/linux/irqchip/arm-gic-v3.h`.
- `gic_do_wait_for_rwp()`: returns `void`; it uses
  `readl_relaxed_poll_timeout_atomic()` and only prints on `-ETIMEDOUT`.
- `gic_redist_wait_for_rwp()`: polls one frame, the calling CPU's
  (`gic_data_rdist()` is `this_cpu_ptr()`), not every redistributor.
- Waits in `drivers/irqchip/irq-gic-v3.c`: after the enable-clear write in
  `gic_mask_irq()`, after each `GICD_CTLR` write in `gic_dist_init()`, and
  after `gic_cpu_config()` in `gic_cpu_init()`; no other write is followed by
  one.
- `gic_set_affinity()`: waits only inside `gic_mask_irq()`, and only when the
  interrupt was enabled; nothing waits after the `GICD_IROUTER` write, although
  the comment before its `gic_unmask_irq()` call speaks of waiting.
- `redist_disable_lpis()` in `drivers/irqchip/irq-gic-v3-its.c`: has its own
  loop on `GICR_CTLR_RWP` and, unlike the helpers above, returns `-ETIMEDOUT`.
- **Potentially unsafe usage**: `gic_redist_wait_for_rwp()` after a
  redistributor write.
  - Unsafe: when the write went to another CPU's frame, or the task can
    migrate between write and wait; the poll then reads a frame that was not
    written and can return at once.
  - Safe: write through `gic_data_rdist_sgi_base()` and wait on the same CPU
    without migration, as `gic_cpu_init()` does from `gic_starting_cpu()`; the
    `this_cpu_ptr()` in `gic_data_rdist()` defines the requirement.
