- Range with a domain: `WARN_ON()`, then one `irq_create_mapping()` of the
  cell's `start`; `start` and `end` of the child both get that number. There
  is no loop over the range.
- `DEFINE_RES_IRQ()` and `DEFINE_RES_IRQ_NAMED()`: always describe one
  interrupt; a range needs explicit `.start` and `.end`, or
  `DEFINE_RES_NAMED()` with a size.
- Failed mapping: `irq_create_mapping()` returns 0 and the core stores it
  unchecked; the child's `platform_get_irq()`, when it takes the number from
  that resource, then warns and returns `-EINVAL`.
- No domain and `irq_base` 0: the numbers pass through unchanged, and they
  need not be Linux irq numbers.
  - For example, `drivers/mfd/wm831x-core.c` passes chip-relative numbers,
    and its children map them with `wm831x_irq()`.
