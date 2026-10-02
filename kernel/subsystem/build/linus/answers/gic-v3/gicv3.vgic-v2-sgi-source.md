- Exit for the next source: `ICH_LR_EOI` in the LR, set by
  `vgic_v3_compute_lr()` when `irq->source` has bits besides the chosen one;
  `ICH_HCR_EL2_NPIE` is not used for this.
- `vgic_flush_lr_state()`: no special case; the SGI takes one LR, is counted
  once, and lower-priority entries behind it are still loaded.
- SGI active with sources pending: the LR carries active state with
  `irq->active_source` in the CPUID field, `ICH_LR_EOI`, and no pending bit.
- Next source is loaded by a later flush, once `irq->active` is clear.
- `vgic_v3_fold_lr()` on a v2 SGI: active LR writes CPUID to
  `irq->active_source`; pending LR sets the CPUID bit back in `irq->source`.
- Pending with `irq->source == 0`: `WARN_RATELIMIT()`, `vgic_v3_compute_lr()`
  returns 0; `vgic_v3_populate_lr()` stores that 0 in the LR and still sets
  `on_lr`.
