- `gicv5_ppi_irq_set_type()`: installed as `.irq_set_type` of
  `gicv5_ppi_irq_chip`.
- `gicv5_ppi_irq_set_type()` returns `-EINVAL` when the request has a bit of
  `IRQ_TYPE_EDGE_BOTH` and the hardware says level, or a bit of
  `IRQ_TYPE_LEVEL_MASK` and the hardware says edge.
- `gicv5_ppi_irq_set_type()` returns 0 otherwise, including for
  `IRQ_TYPE_NONE`; it writes no register.
- Polarity is not compared: high and low level both pass on a level PPI,
  rising and falling both pass on an edge PPI.
- `gicv5_ppi_irq_is_level()`: a set bit in the handling-mode register means
  level.
- Reported trigger: `gicv5_irq_domain_translate()` with
  `GICV5_HWIRQ_TYPE_PPI` discards the trigger from the firmware specifier.
- Specifier format in `gicv5_irq_domain_translate()`: an OF node needs at
  least 3 cells.
