- `gpiochip_remove()`: has no test for requested lines and prints nothing
  about them; it returns `void`. Its kerneldoc says such a chip "may not be
  removed", but no code enforces that.
- Released by removal itself, while the chip is still set: lines requested
  through sysfs, flagged `GPIOD_FLAG_SYSFS` (`gpiochip_sysfs_unregister()`),
  hogs, and every interrupt requested on a line flagged
  `GPIOD_FLAG_USED_AS_IRQ`.
- `gpiochip_free_remaining_irqs()`: calls `free_irq()` on the consumers'
  behalf for each action on such a line.
- Order: `gdev->chip` is cleared and `synchronize_srcu(&gdev->srcu)` runs
  before `gpiochip_irqchip_remove()`, `acpi_gpiochip_remove()` and
  `of_gpiochip_remove()`; the character device goes last.
- `gpiod_get_value()` on a removed chip: returns `-ENODEV`; nothing is
  logged about the missing chip.
- `gpiod_set_value()` and the other setters: return `int`;
  `gpiod_set_raw_value_commit()` tests `GPIOD_FLAG_IS_OUT` before the chip,
  so a line not flagged output gives `-EPERM`, otherwise `-ENODEV`.
- Calls that never look at the chip still succeed, for example
  `gpiod_cansleep()`, `gpiod_is_active_low()` and
  `gpiod_set_consumer_name()`.
- `gpiod_free()` after removal: `gpiod_free_commit()` does nothing when
  `guard.gc` is NULL, so `gc->free()` is never called for a line still
  requested once `gdev->chip` is cleared; only the module and device
  references drop.
- `gpiochip_get_data()` after removal: `gpiochip_remove()` sets
  `gdev->data` to NULL after the SRCU wait, never clears `gc->gpiodev`, and
  then drops its reference, which may free the `struct gpio_device`.
- Driver code that runs after removal, such as its own IRQ handler or work
  item, therefore cannot use `gpiochip_get_data()` or `gc->gpiodev`.
- `irq_chip` callbacks: reached through the IRQ core, not through
  `gdev->srcu`; they can still run inside `gpiochip_remove()` after the
  `gpio_chip` callbacks have stopped.
- Domain added with `gpiochip_irqchip_add_domain()`:
  `gpiochip_irqchip_remove()` neither disposes its mappings nor removes it;
  whoever created the domain does, for example `regmap_del_irq_chip()`.
