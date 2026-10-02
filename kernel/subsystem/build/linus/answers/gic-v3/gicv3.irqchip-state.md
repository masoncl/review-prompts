- ID test: `d->hwirq >= 8192` is the only one, in both
  `gic_irq_set_irqchip_state()` and `gic_irq_get_irqchip_state()`; SGIs pass
  it, for every state.
- Comments beside the test ("SGI/PPI/SPI only", "PPI/SPI only"): narrower
  than the test; EPPI and ESPI pass too.
- Error code: `-EINVAL` is the only one, for an LPI and for an unknown
  `which`.
- Read-back: only after a write of `GICD_ISACTIVER` (set active), by
  `gic_peek_irq()` on the same register; not after `GICD_ICACTIVER` or a
  pending write.
- Reason given in the comment in `gic_irq_set_irqchip_state()`: the active
  state must have taken effect so that it cannot race with a guest-driven
  deactivation.
- Redistributor interrupt (`gic_irq_in_rdist()`): `gic_peek_irq()` and
  `gic_poke_irq()` use `gic_data_rdist_sgi_base()`, so state is read and
  written for the calling CPU only.
- LPI set, for a device LPI (`its_irq_chip`): handled by
  `its_irq_set_irqchip_state()` in `drivers/irqchip/irq-gic-v3-its.c`, which
  accepts only `IRQCHIP_STATE_PENDING`.
- LPI get: `its_irq_chip` has no `irq_get_irqchip_state`, so
  `__irq_get_irqchip_state()` walks to the parent and
  `gic_irq_get_irqchip_state()` returns `-EINVAL`.
