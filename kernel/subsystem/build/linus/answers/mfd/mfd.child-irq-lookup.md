- Call chain: `platform_get_irq()` calls `platform_get_irq_optional()`, which
  calls `platform_get_irq_affinity()` with a NULL affinity pointer.
- Affinity: filled by `get_irq_affinity()` in `drivers/base/platform.c`, only
  when the result is > 0 and the pointer is non-NULL.
- By name: `__platform_get_irq_byname()` does not call `of_irq_get_byname()`;
  it calls `fwnode_irq_get_byname()` on `dev_fwnode()`.
  - An ACPI node whose `interrupt-names` holds the name therefore also wins
    over the cell resource.
- Child with both an OF node and an ACPI node: `dev_fwnode()` returns the OF
  node whenever `dev->of_node` is set, so the lookup takes the OF path.
- ACPI node, by index: the cell resource wins.
  - `acpi_irq_get()`: runs only when that resource has `IORESOURCE_DISABLED`.
  - `acpi_dev_gpio_irq_get()`: the last step, only for index 0 and only when
    there is no IRQ resource at that index.
- Result 0: `WARN()` and `-EINVAL`, not `-ENXIO`, in both the index path and
  the name path.
