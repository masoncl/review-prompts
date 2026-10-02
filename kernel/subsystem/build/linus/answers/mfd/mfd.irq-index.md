- `regmap_irq_get_virq()` has no bounds test: it reads
  `data->chip->irqs[irq].mask` for any `irq`, including negative values and
  values `>= chip->num_irqs`.
- Return on mapping failure: 0 from `irq_create_mapping()`, not a negative
  errno. `-EINVAL` is returned only for a table entry whose `mask` is 0.
- `irq_create_mapping()` on the domain is bounds-checked by
  `irq_domain_associate_locked()` against `hwirq_max` (`chip->num_irqs`), but
  `regmap_irq_get_virq()` reads the table before it gets there.
- **Potentially unsafe usage**: passing `regmap_irq_get_virq()` an index that
  is not a constant.
  - Unsafe: when nothing limits the value to `0 .. chip->num_irqs - 1` of the
    chip behind `data`, for example a value from firmware, a negative errno,
    or an enum that belongs to another chip variant; the read goes outside
    `chip->irqs[]`.
  - Safe: an index the parent itself placed in the cell resource from the enum
    that indexes `chip->irqs[]`, read back after the `< 0` test, as
    `axp20x_usb_power_probe()` does; only while the child's firmware node
    gives no interrupt of that name, since `__platform_get_irq_byname()` asks
    firmware first.
  - Safe: a loop bounded by the driver's own table of indices from the enum
    that indexes `chip->irqs[]` of that chip, as `max77693_muic_probe()` in
    `drivers/extcon/extcon-max77693.c` does with `enum max77693_irq_muic`.
