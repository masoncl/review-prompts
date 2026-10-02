- What `platform_get_irq()` returns to a child is decided by the last two
  arguments the parent gives `mfd_add_devices()`; the cell resource holds the
  chip index in every case:

| Parent passes | Resource after `mfd_add_device()` | Child |
|---|---|---|
| `domain` from `regmap_irq_get_domain()` | Linux interrupt number | requests it directly |
| `irq_base` from `regmap_irq_chip_get_base()`, `domain` NULL | `irq_base` + index | requests it directly |
| `irq_base` 0, `domain` NULL | chip index, unchanged | converts with `regmap_irq_get_virq()` |

- `irq_base` row: correct only for a chip registered with a non-zero
  `irq_base`; `regmap_irq_chip_get_base()` does `WARN_ON()` and returns 0
  otherwise. Example: `da9063_device_init()` in `drivers/mfd/da9063-core.c`.
- Index row: `axp20x_usb_power_probe()` in
  `drivers/power/supply/axp20x_usb_power.c` feeds the result of
  `platform_get_irq_byname()` to `regmap_irq_get_virq()`; its parent in
  `drivers/mfd/axp20x.c` passes `0, NULL`.
- `regmap_irq_get_virq()` with a constant: used when the cell has no IRQ
  resource and the child reaches the parent's `struct regmap_irq_chip_data`,
  and by a parent that needs a child interrupt itself, for example
  `sec_irq_init_s2mpg1x()` through `s2mpg1x_add_chained_pmic()` in
  `drivers/mfd/sec-irq.c`.
- Child with an OF node: `platform_get_irq_affinity()` in
  `drivers/base/platform.c` tries `of_irq_get()` first and
  `__platform_get_irq_byname()` tries `fwnode_irq_get_byname()` first. The cell
  resource is used only when firmware gives no interrupt.
