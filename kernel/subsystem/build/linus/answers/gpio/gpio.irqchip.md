- `IRQCHIP_IMMUTABLE` chip: `gpiochip_set_irq_hooks()` returns at once and
  gpiolib validates nothing in it; `const` is not required;
  `gpio_irq_chip_set_chip()` casts it away.
- `GPIOCHIP_IRQ_RESOURCE_HELPERS`: installs `gpiochip_irq_reqres()` and
  `gpiochip_irq_relres()`, the `struct irq_data` forms of
  `gpiochip_reqres_irq()` and `gpiochip_relres_irq()`.
- Flag names: `GPIOD_FLAG_USED_AS_IRQ` and `GPIOD_FLAG_IRQ_IS_ENABLED` in
  `drivers/gpio/gpiolib.h`; there is no FLAG_USED_AS_IRQ or
  FLAG_IRQ_IS_ENABLED.
- `gpiochip_enable_irq()` and `gpiochip_disable_irq()`: `WARN_ON()` and do
  nothing when the line lacks `GPIOD_FLAG_USED_AS_IRQ`, which
  `gpiochip_lock_as_irq()` sets, for example from the resource helpers or
  from `gpiochip_irq_domain_activate()`.
- Immutable chip that omits the resource helpers and the enable/disable
  calls, when nothing else calls `gpiochip_lock_as_irq()` for the line (a
  hierarchical domain does, in `gpiochip_irq_domain_activate()`):
  `GPIOD_FLAG_USED_AS_IRQ` is never set, so
  `gpiod_direction_output_nonotify()` does not refuse the line and
  `gpiochip_free_remaining_irqs()` skips it.
- Driver with `irq_enable` or `irq_disable`: `irq_enable()` and
  `__irq_disable()` in `kernel/irq/chip.c` call those instead of
  `irq_unmask` and `irq_mask`, so the gpiolib calls go there.
- Mutable chip, resource callbacks: filled in only when both are NULL; when
  the driver set either, nothing is logged about that and hooking continues.
- Mutable chip, hooks: two independent choices, never all four.
  `irq_disable` is wrapped if set, else `irq_mask`; `irq_enable` is wrapped
  if set, else `irq_unmask`.
- `gc->irq.irq_enable` already set by the driver: `WARN_ON()` and no enable,
  disable, mask or unmask hook is installed.
- Chained `parent_handler` with `gc->can_sleep`: refused only in
  `gpiochip_add_irqchip()`, which tests it only when `gc->irq.chip` is set.
- `gpiochip_irqchip_add_domain()`: has no `can_sleep` test; under
  `CONFIG_GPIOLIB_IRQCHIP` it returns `-EINVAL` only for a NULL domain.
