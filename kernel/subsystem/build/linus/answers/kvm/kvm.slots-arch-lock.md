- May be taken inside a `kvm->srcu` read side section:
  `kvm_swap_active_memslots()` unlocks it before
  `synchronize_srcu_expedited()`.
- Holder without `slots_lock`: take the lock, then read the memslots pointer,
  and keep the lock until every change to those memslots is complete, as
  `mmu_first_shadow_root_alloc()` in `arch/x86/kvm/mmu/mmu.c` does.
- `kvm_set_memslot()`: returns with the lock released on every path.
- `kvm_arch_prepare_memory_region()` runs with the lock held;
  `kvm_arch_commit_memory_region()` runs without it, so a holder of the lock
  can change `new->arch` while it runs.
- `kvm_invalidate_memslot()`: retakes the lock after the first swap and copies
  `invalid_slot->arch` back to `old->arch`, to pick up changes made while it
  was dropped.
- s390 takes it too: it serialises CMMA migration state in
  `arch/s390/kvm/s390/s390.c`, for example `kvm_s390_vm_set_migration()`.
