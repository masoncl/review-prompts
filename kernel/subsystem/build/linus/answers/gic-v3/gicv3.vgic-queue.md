- `irq->ops->queue_irq_unlock`: tested first; if set,
  `vgic_queue_irq_unlock()` returns its result and does nothing else.
- `vgic_v5_ppi_queue_irq_unlock()` in `arch/arm64/kvm/vgic/vgic-v5.c` is the
  only implementation: drops `irq_lock`, kicks `irq->target_vcpu`, returns
  true, never touches an ap_list or a reference.
- Reference: taken with `vgic_get_irq_ref()` from
  `arch/arm64/kvm/vgic/vgic.h`; there is no vgic_get_irq_kref() here.
- `vgic_get_irq_ref()` on an SGI, PPI or SPI of a GICv2 or GICv3 guest:
  no-op; `irq->refcount` changes only for `intid >= VGIC_MIN_LPI`.
- Caller's own reference: required; `vgic_get_irq_ref()` uses
  `refcount_inc_not_zero()` and only does `WARN_ON_ONCE()` on failure, then
  the interrupt is queued anyway.
