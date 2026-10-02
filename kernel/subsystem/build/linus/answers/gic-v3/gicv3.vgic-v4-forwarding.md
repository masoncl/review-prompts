- Exits that return 0 without mapping, in order:
  1. `vgic_supports_direct_msis()` is false
  2. `vgic_get_its()` returns an error; see `vgic_msi_to_its()` in
     `arch/arm64/kvm/vgic/vgic-its.c`
  3. `vgic_its_resolve_lpi()` returns non-zero, whatever the value
  4. `irq->hw` is already set
- `vgic_supports_direct_msis()`: also false on a host where
  `system_supports_direct_sgis()` is true and the VM's `nassgicap` is clear,
  so clearing vSGI support for a VM turns off vLPI forwarding too.
- `its_map_vlpi()` failure: returned to the caller as an error, with `irq->hw`
  left false; the comment above the call says "silently bail out", the code
  does not.
- `its->its_lock`: taken with `guard(mutex)` after `vgic_get_its()`, held to
  the end of the function.
- `irq->irq_lock`: taken with `raw_spin_lock_irqsave()` before the `irq->hw`
  test and held across `its_map_vlpi()`, so the ITS driver runs with
  interrupts off.
- `vgic_its_resolve_lpi()`: returns `ite->irq` without a reference for the
  caller; `its->its_lock` keeps the ITE and its reference alive, and
  `kvm_vgic_v4_set_forwarding()` calls no `vgic_put_irq()`.
- Pending transfer, only when `irq->pending_latch` is set:
  `irq_set_irqchip_state()` reaches `its_irq_set_irqchip_state()`, which
  sends `its_send_vint()` because the irq is now forwarded; it is an ITS
  command, not a write to the pending table.
- Pending transfer failure: `WARN_RATELIMIT()`, then the error is returned
  with `irq->hw` still true and the vLPI still mapped.
- After the transfer: `pending_latch` is cleared and the lock is dropped
  inside `vgic_queue_irq_unlock()`, not at the `out_unlock_irq` label.
