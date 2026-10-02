- Kept alive by an extra reference: `vgic_get_irq_ref()` is called under
  `irq_lock`, before `irq_lock` and `ap_list_lock` are dropped.
- Extra reference dropped with `vgic_put_irq_norelease()`, not
  `vgic_put_irq()`, after all three locks are released.
- A dropped-to-zero LPI is freed later by `vgic_release_deleted_lpis()`, which
  takes `lpi_xa.xa_lock`, after the walk has released `ap_list_lock`.
- Check before the move: `irq->vcpu == vcpu && target_vcpu ==
  vgic_target_oracle(irq)`; `target_vcpu` is the value from before the unlock.
- `goto retry` runs after the move and after a failed check alike.
- `active_spis`: not touched by `vgic_prune_ap_list()`.
- **Unsafe usage**: moving the interrupt after the relock on the oracle
  comparison alone.
  - Unsafe: the entry may have left this list in the window
    (`vgic_flush_pending_lpis()` does `list_del()` and clears `irq->vcpu`), so
    `list_del()` runs on an entry that is not on `vcpu`'s list.
  - Safe: test `irq->vcpu == vcpu` as well, with both `ap_list_lock`s and
    `irq_lock` held, as `vgic_prune_ap_list()` does; `vgic_target_oracle()`
    asserts `irq_lock`.
- **Unsafe usage**: continuing the `list_for_each_entry_safe()` walk after
  `ap_list_lock` was dropped.
  - Unsafe: `tmp` was read before the unlock and may be off the list.
  - Safe: restart from the head, as `vgic_prune_ap_list()` does with
    `goto retry`.
