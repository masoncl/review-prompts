- Register names: there are no IWB_WENABLER, IWB_WTMR or IWB_WENABLE_STATUSR
  definitions; the tree has `GICV5_IWB_WENABLER`, `GICV5_IWB_WTMR` and
  `GICV5_IWB_WENABLE_STATUSR` in `include/linux/irqchip/arm-gic-v5.h`.
- `gicv5_iwb_irq_enable()`: writes the wire bit, then calls
  `irq_chip_enable_parent()`; `gicv5_iwb_irq_disable()` clears it, then
  calls `irq_chip_disable_parent()`.
- Parent of enable/disable: `gicv5_its_irq_chip` has no `irq_enable` or
  `irq_disable`, so the parent helpers end in the LPI unmask and mask.
- Poll of `GICV5_IWB_WENABLE_STATUSR`: only `__gicv5_iwb_set_wire_enable()`
  and the probe poll it, through `gicv5_iwb_wait_for_wenabler()`.
- `gicv5_iwb_set_type()`: no wait after the `GICV5_IWB_WTMR` write; it
  returns 0 straight after `iwb_writel_relaxed()`.
- Wait errors in `gicv5_iwb_set_type()`: none exist; its only failures are
  `-EINVAL` for a register index >= `nr_regs` and for an unhandled type.
- Trigger encoding in `GICV5_IWB_WTMR`:

| Requested type | Wire bit |
|---|---|
| `IRQ_TYPE_LEVEL_HIGH`, `IRQ_TYPE_LEVEL_LOW` | set |
| `IRQ_TYPE_EDGE_RISING`, `IRQ_TYPE_EDGE_FALLING` | cleared |
| anything else, for example `IRQ_TYPE_EDGE_BOTH` | `-EINVAL`, no write |

- Polarity: not programmed; high and low, rising and falling are treated
  alike.
- Failed wait in enable/disable: `gicv5_iwb_irq_enable()` and
  `gicv5_iwb_irq_disable()` ignore the return value of
  `__gicv5_iwb_set_wire_enable()` and still call the parent helper.
- Out-of-range wire in enable/disable: the `-EINVAL` from the `nr_regs`
  check is ignored the same way, so the LPI is still unmasked or masked.
