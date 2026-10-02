- Lookup: `vgic_get_vcpu_irq()` returns the interrupt or NULL; on NULL
  `vgic_v3_fold_lr()` returns at once.
- Lookup reference: dropped by `vgic_put_irq()` at the end.

| Kind | Taken from the LR |
|---|---|
| LPI (`intid >= VGIC_MIN_LPI`) | active bit discarded, `irq->active` = false |
| others | `irq->active` = `ICH_LR_ACTIVE_BIT` |
| edge | pending bit set: `pending_latch = true`; fold never clears it |
| level | both `ICH_LR_STATE` bits clear: `pending_latch = false`; `line_level` not taken from the LR |
| mapped level | `vgic_irq_handle_resampling()`, below |

- `vgic_irq_handle_resampling()`, ordinary mapped level: re-reads the
  physical line when the LR is still pending, or when deactivated with
  `irq->line_level` set; clears physical active if the line is low.
- `deactivated`: `irq->active` was set before the fold and the LR's active
  bit is clear.
- `kvm_notify_acked_irq()` in `vgic_v3_fold_lr()`: called when `deactivated`,
  `lr_signals_eoi_mi()` and `vgic_valid_spi()` all hold.
- The notification runs after `irq_lock` is released and before
  `vgic_put_irq()`.
- `vgic_v2_fold_lr()` in `arch/arm64/kvm/vgic/vgic-v2.c`: notifies on
  `lr_signals_eoi_mi()` and `vgic_valid_spi()` alone, before its lookup.
