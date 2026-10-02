- Signature: `void kvm_vgic_v4_unset_forwarding(struct kvm *kvm, int
  host_irq)`; it takes no routing entry and returns nothing.
- Lookup: `__vgic_host_irq_get_vlpi()` in `arch/arm64/kvm/vgic/vgic-v4.c`
  walks `kvm->arch.vgic.lpi_xa` under `guard(rcu)` for an entry with
  `irq->hw` set and `irq->host_irq == host_irq`.
- Lookup does not call `vgic_get_its()`, `vgic_its_resolve_lpi()` or
  `its_get_vlpi()`.
- Reference: taken with `vgic_try_get_irq_ref()`; if that fails the helper
  returns NULL without looking further.
- Not forwarded: no entry matches, the helper returns NULL and the function
  returns having changed nothing; same when `vgic_supports_direct_msis()` is
  false.
- Found: under `irq->irq_lock`, re-tests `irq->hw`, then `atomic_dec()` of the
  target vPE's `vlpi_count`, `irq->hw = false`, `its_unmap_vlpi()`.
- `irq->host_irq`: not cleared.
- `its_unmap_vlpi()`: returns `void`; a failing `irq_set_vcpu_affinity()` only
  hits `WARN_ON_ONCE()`.
- `its->its_lock`: not taken; `kvm_irq_routing_update()` in
  `virt/kvm/eventfd.c` reaches this function through
  `kvm_arch_update_irqfd_routing()` with `kvm->irqfds.lock` held, so nothing
  on this path may sleep.
- `kvm_arch_update_irqfd_routing()`: on a changed MSI route it only unmaps;
  it does not map the new route.
