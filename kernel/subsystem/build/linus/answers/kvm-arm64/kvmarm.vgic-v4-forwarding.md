- `kvm_vgic_v4_set_forwarding()` returns 0 without mapping when:
  - `vgic_supports_direct_msis()` is false;
  - `vgic_get_its()` returns an error pointer;
  - `vgic_its_resolve_lpi()` fails;
  - `irq->hw` is already set.
- Errors returned by set: from `its_map_vlpi()`, and from
  `irq_set_irqchip_state()` when the pending state is transferred.
- Set, locks: `its->its_lock`, then `irq_lock` with IRQs off.
- Set, state: `irq->hw`, `irq->host_irq`, and `vlpi_count` of the target
  `struct its_vpe`.
- Set takes no reference; the ITE's reference holds under `its_lock`.
- `kvm_vgic_v4_unset_forwarding()`: returns `void`, takes `(kvm, host_irq)`.
- Unset, checks: `vgic_supports_direct_msis()`, then
  `__vgic_host_irq_get_vlpi()`, which scans `lpi_xa` under RCU for `hw` set
  and a matching `host_irq`.
- Unset, locks: `irq_lock` with IRQs off; it does not take `its_lock`.
- Unset, state: under `irq_lock`, decrements `vlpi_count`, clears `irq->hw`,
  calls `its_unmap_vlpi()`; then drops the lookup reference with
  `vgic_put_irq()`.
- `kvm_arch_update_irqfd_routing()`: calls unset under `kvm->irqfds.lock`, a
  spinlock taken in `virt/kvm/eventfd.c`; unset must not sleep.
