- PMR values: `GIC_PRIO_IRQON` is `GICV3_PRIO_UNMASKED` (IRQs enabled),
  `GIC_PRIO_IRQOFF` is `GICV3_PRIO_IRQ` (IRQs masked, NMIs pass); see
  `arch/arm64/include/asm/ptrace.h`.
- The flag is named `GICV3_PRIO_PSR_I_SET`; there is no GICV3_PRIO_PSR_I.
- `dist_prio_irq` and `dist_prio_nmi`: `static` in
  `drivers/irqchip/irq-gic-v3.c`, so no other file can use them.
- LPIs: `gic_init_bases()` passes `dist_prio_irq` to `its_init()`, which
  stores it in `lpi_prop_prio` in `drivers/irqchip/irq-gic-v3-its.c`; ITS code
  uses that variable for the property table.
- `irqs_priority_unmasked()`: with `system_uses_irq_prio_masking()`, compares
  the saved PMR for equality with `GIC_PRIO_IRQON`, so
  `GIC_PRIO_IRQON | GIC_PRIO_PSR_I_SET` counts as masked.

| `static_assert()` | Holds exactly when | Code that relies on it |
|---|---|---|
| `__gicv3_prio_valid_ns()` of `GICV3_PRIO_NMI` and of `GICV3_PRIO_IRQ` | bit 7 of the constant is set | `gic_prio_init()`: the left-shifted value, once the GIC shifts it right and sets bit 7, is the constant again |
| `GICV3_PRIO_NMI < GICV3_PRIO_IRQ` | as written | `gic_pmr_mask_irqs()`: PMR at `GIC_PRIO_IRQOFF` masks IRQs and passes NMIs |
| `GICV3_PRIO_IRQ < GICV3_PRIO_UNMASKED` | as written | PMR at `GIC_PRIO_IRQON` admits IRQs |
| `GICV3_PRIO_IRQ < (GICV3_PRIO_IRQ \| GICV3_PRIO_PSR_I_SET)` | bit 4 of `GICV3_PRIO_IRQ` is clear | `local_daif_mask()`: its debug `WARN_ON()` compares the PMR with `GIC_PRIO_IRQOFF \| GIC_PRIO_PSR_I_SET`, which must differ from `GIC_PRIO_IRQOFF` |

- Not asserted: the order of the shifted values, and the round trip of
  `GICV3_PRIO_UNMASKED`, which is never written to a distributor or
  redistributor.
