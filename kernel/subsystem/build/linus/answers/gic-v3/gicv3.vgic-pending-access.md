- hw SGI below means `irq->hw && vgic_irq_is_sgi(irq->intid)`; it is tested
  before the other `irq->hw` tests in all three helpers and ignores
  `is_user`.

| Access | Interrupt | Guest | Userspace |
|---|---|---|---|
| read | hw SGI | physical `IRQCHIP_STATE_PENDING` | same |
| read | mapped level | `vgic_get_phys_line_level()`, latch ignored | as other |
| read | other | `irq_is_pending()` | vGICv3 `irq->pending_latch`; vGICv2 `irq_is_pending()` |
| set | hw SGI | physical pending set, latch untouched | same |
| set | other `irq->hw` | latch set, physical active set | latch set only |
| clear | hw SGI | physical pending cleared | same |
| clear | other `irq->hw` | `vgic_hw_irq_cpending()` | latch cleared only |

- `__read_pending()` on a hw SGI: calls `irq_get_irqchip_state()`; it does
  not call `vgic_v4_get_vlpi_state()`.
- `__set_pending()` from the guest on a mapped interrupt: sets physical
  active with `vgic_irq_set_phys_active()`, not physical pending.
- `vgic_hw_irq_cpending()`: clears the latch and physical pending always,
  physical active only when `!irq->active`.
- Mapped edge interrupt: read as "other"; the write rows test `irq->hw`
  only, so they apply to it.
- vGICv3 userspace write of `GICD_ISPENDR` or `GICR_ISPENDR0`:
  `vgic_v3_uaccess_write_pending()` calls `vgic_uaccess_write_spending()`
  with `val`, then `vgic_uaccess_write_cpending()` with `~val`; both helpers
  run with `is_user` true.
- A vGICv3 userspace write of `GICR_ISPENDR0` therefore clears physical
  pending of every hw SGI whose bit is 0.
- vGICv2 userspace: `vgic_uaccess_write_spending()` and
  `vgic_uaccess_write_cpending()` are the register handlers themselves; see
  `arch/arm64/kvm/vgic/vgic-mmio-v2.c`.
