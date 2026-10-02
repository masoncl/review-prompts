- `ICH_LR_HW`: set when `irq->hw && !vgic_irq_needs_resampling(irq)`; GICv2
  SGI handling plays no part.
- `vgic_irq_needs_resampling()` interrupt: takes the non-HW branch, so a level
  one gets `ICH_LR_EOI`.
- Pending withheld only when `irq->active` and one of:
  - `vgic_irq_is_multi_sgi()`;
  - the `ICH_LR_HW` case;
  - non-HW branch with `VGIC_CONFIG_LEVEL`.
- `line_level` being low does not withhold pending by a test of its own; it
  only enters through `irq_is_pending()`.
- `on_lr` in `vgic_v3_compute_lr()`: `WARN_ON(irq->on_lr)` only; the value is
  still computed and returned.
- `vgic_flush_lr_state()` has no `on_lr` test besides that `WARN_ON()`; it
  relies on each interrupt being one ap_list entry and on fold having cleared
  `on_lr`.
- `vgic_v3_compute_lr()` callers that build a pseudo-LR:
  `vgic_v3_fold_lr_state()` and `vgic_v3_deactivate()`.
- **Unsafe usage**: building a pseudo-LR for an interrupt whose `on_lr` is
  set.
  - Unsafe: the real LR holds the state; folding the pseudo-LR overwrites
    `irq->active` and clears `on_lr` while the LR is live.
  - Safe: test `irq->on_lr` under `irq_lock` first, as `vgic_v3_deactivate()`
    does.
  - Safe: walk only entries after `last_lr_irq`, after every used LR was
    folded, as `vgic_v3_fold_lr_state()` does.
