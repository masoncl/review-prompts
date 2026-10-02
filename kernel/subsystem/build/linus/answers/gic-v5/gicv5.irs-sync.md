- `gicv5_irs_syncr()`: returns void; a timeout is only logged by the poll
  helper.
- Poll: `gicv5_wait_for_op()`, the sleeping variant, so the caller must be
  able to sleep.
- IRS addressed: takes no argument; always the first entry of `irs_nodes`;
  `WARN_ON_ONCE()` and return when the list is empty.
- Other IRSs: never written with `GICV5_IRS_SYNCR`.
- Only caller: `gicv5_its_irq_domain_free()`, as its last step, after
  `irq_domain_free_irqs_parent()` and `gicv5_its_syncr()`.
- Invalidation: `include/linux/irqchip/arm-gic-v5.h` defines no IRS
  invalidate register; `GICV5_ITS_INV_EVENTR` and `GICV5_ITS_INV_DEVICER`
  belong to the ITS.
