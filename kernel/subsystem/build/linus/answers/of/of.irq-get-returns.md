- No interrupt at that index: `of_irq_get()` returns `-EINVAL` when the node
  has no `interrupts` property or no interrupt parent, `-EOVERFLOW` when the
  index is past the end of `interrupts`.
- `-ENOENT`: comes from `of_irq_parse_raw()` when the walk runs out of
  parents without reaching a controller; it does not mean "property absent".
- `platform_get_irq_affinity()` in `drivers/base/platform.c`: passes on only
  a positive value or `-EPROBE_DEFER` from `of_irq_get()`; anything else
  falls back to the resource table and, with no IRQ resource there, ends as
  `-ENXIO`.
- `platform_get_irq_optional()` and `platform_get_irq()`: wrappers around
  `platform_get_irq_affinity()`, which turns a final 0 into `-EINVAL` with a
  `WARN()`.
- `fwnode_irq_get()` in `drivers/base/property.c`: turns 0 from
  `of_irq_get()` into `-EINVAL`.
