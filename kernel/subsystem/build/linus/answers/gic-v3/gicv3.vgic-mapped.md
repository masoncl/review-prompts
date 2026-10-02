- `kvm_vgic_map_phys_irq()`: takes three arguments (vcpu, host irq, virtual
  INTID); there is no `struct irq_ops` argument.
- `kvm_vgic_map_irq()`: besides `irq->hw`, `irq->host_irq` and
  `irq->hwintid`, it calls `irq->ops->set_direct_injection(vcpu, irq, true)`
  when the installed ops has that callback.
- Already mapped interrupt: not rejected; the three fields are overwritten.
- `-EINVAL` from the map: only when `irq_to_desc(host_irq)` returns NULL.
- INTID type: `kvm_vgic_map_phys_irq()` makes no PPI/SPI test, only
  `BUG_ON(!irq)`; the PPI/SPI test is in `kvm_vgic_set_owner()`.
- Reset: `kvm_timer_vcpu_reset()` calls `kvm_vgic_reset_mapped_irq()` only
  when `timer->enabled` and `irqchip_in_kernel()`; it first calls
  `kvm_timer_update_irq(vcpu, false, ...)` for every timer.
- Injection is gated by `irq->owner`, not by `irq->hw`:
  `vgic_validate_injection()` never looks at `irq->hw`, and the map sets no
  owner.
- Owner mismatch: `kvm_vgic_inject_irq()` drops the request and returns 0,
  not an error; `KVM_IRQ_LINE` and irqfd pass `NULL` and get that 0.
- GICv5 VM: `kvm_timer_update_irq()` returns before `kvm_vgic_inject_irq()`
  for `map.direct_vtimer` and `map.direct_ptimer`; the timer does not inject
  those in software.
