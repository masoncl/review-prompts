- Reason for the wait: the notifier callbacks change
  `mmu_invalidate_in_progress` only when a memslot overlaps the range
  (`on_lock` in `kvm_handle_hva_range()`), so a swap between start and end
  would leave it unbalanced.
- `mn_active_invalidate_count`: raised by every start, whether or not a
  memslot overlaps.
- `kvm_swap_active_memslots()`: waits until `mn_active_invalidate_count` is
  zero before it publishes the new memslots, with an open-coded
  `prepare_to_rcuwait()` / `schedule()` loop in `TASK_UNINTERRUPTIBLE`, not
  `rcuwait_wait_event()`.
- `rcu_assign_pointer()` on `kvm->memslots[as_id]`: done with
  `mn_invalidate_lock` still held, so no start can slip in between the check
  and the store.
- `kvm_destroy_vm()`: zeroes a nonzero `mn_active_invalidate_count` after
  `mmu_notifier_unregister()`, since the matching end will never run.
