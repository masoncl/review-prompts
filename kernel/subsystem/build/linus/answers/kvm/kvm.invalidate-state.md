- There is no kvm_mmu_invalidate_begin() in this tree; the function is
  `kvm_mmu_invalidate_start()` in `virt/kvm/kvm_main.c`.
- Range reset: `kvm_mmu_invalidate_start()` sets `mmu_invalidate_range_start`
  and `mmu_invalidate_range_end` to `INVALID_GPA`, and only when the count
  goes from 0 to 1.
- `kvm_mmu_invalidate_end()`: never writes the range; after the last end the
  fields keep the last union until the next 0 to 1 start.
- Several adds per invalidation: x86 `kvm_arch_pre_set_memory_attributes()`
  calls `kvm_mmu_invalidate_range_add()` for the hugepage ranges around the
  head and tail, so the recorded range can be wider than the range being
  changed.
