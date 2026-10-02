- Physical ID: `kvm_vgic_map_irq()` walks `data->parent_data` from
  `irq_desc_get_irq_data()` to the root and stores that root `hwirq`; it does
  not call `irq_get_irq_data()` or `irqd_to_hwirq()`.
- `kvm_vgic_unmap_irq()`: writes only `irq->hw = false` and
  `irq->hwintid = 0`.
- `irq->host_irq`: left at its old value by the unmap.
- `irq->ops`: not cleared by the unmap.
- Before clearing, the unmap calls
  `irq->ops->set_direct_injection(irq->target_vcpu, irq, false)` when the ops
  has that callback.
- `kvm_vgic_unmap_phys_irq()`: returns `-EAGAIN` and changes nothing when
  `!vgic_initialized()`; `kvm_vgic_map_phys_irq()` has no such test.
