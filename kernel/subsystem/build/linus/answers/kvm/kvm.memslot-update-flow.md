- `kvm_invalidate_memslot()`: order is copy and flag, `kvm_replace_memslot()`
  on the inactive set, `kvm_swap_active_memslots()`,
  `kvm_arch_flush_shadow_memslot()`, `kvm_arch_guest_memory_reclaimed()`,
  re-take `slots_arch_lock`, copy `invalid_slot->arch` to `old->arch`.
- After `kvm_invalidate_memslot()`: no replay; the active set holds the
  INVALID copy and the inactive set still holds `old`, which is what makes
  the revert possible.
- `kvm_arch_flush_shadow_memslot()`, the replay on the other set and
  `kvm_arch_commit_memory_region()`: run under `slots_lock` with
  `slots_arch_lock` dropped.
- `kvm_arch_memslots_updated()`: called in every swap, after the grace
  period and before the new `generation` is stored.
- Swaps per call: two for `KVM_MR_DELETE` and `KVM_MR_MOVE`, also when
  prepare fails, none when the `invalid_slot` allocation fails; one for
  `KVM_MR_CREATE` and `KVM_MR_FLAGS_ONLY`, none when prepare fails.
- Reverted DELETE/MOVE: the zap done by `kvm_arch_flush_shadow_memslot()` is
  not undone; `old` is live again.
- `invalid_slot`: freed with `kfree()` in `kvm_set_memslot()`, before
  `kvm_commit_memory_region()`, not by the commit step.
