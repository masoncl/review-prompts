- `gicv5_hwirq_eoi()`: issues `gic_insn(cddi, CDDI)` and nothing else.

| Chip | `irq_eoi` does |
|---|---|
| `gicv5_ppi_irq_chip` | forwarded to a vCPU: nothing; else CDDI with `GICV5_HWIRQ_TYPE_PPI` |
| `gicv5_spi_irq_chip` | CDDI with `GICV5_HWIRQ_TYPE_SPI` |
| `gicv5_lpi_irq_chip` | CDDI with `GICV5_HWIRQ_TYPE_LPI` |

- The one priority drop per acknowledge is done by `gicv5_handle_irq()`,
  not by the callback; see "Priority drop".
- **Unsafe usage**: issuing `gic_insn(0, CDEOI)` from an `irq_eoi` callback
  or from a handler reached through `gicv5_handle_irq()`; it is a second
  drop for one acknowledge, and `CDEOI` names no interrupt.
  - Safe: deactivate only, with the acknowledged type and ID, as
    `gicv5_hwirq_eoi()` does.
- Chips stacked on the PPI, SPI or LPI domain: pass eoi down with
  `irq_chip_eoi_parent()`, as `gicv5_ipi_irq_chip` and `gicv5_its_irq_chip`
  do; `timer_irq_eoi()` in `arch/arm64/kvm/arch_timer.c` does so only when
  the PPI is not forwarded.
