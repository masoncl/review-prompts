- There is no KVM_INVALID_PTE_LOCKED here; the locked marker is
  `KVM_INVALID_PTE_TYPE_LOCKED` in the `KVM_INVALID_PTE_TYPE_MASK` field,
  tested by `stage2_pte_is_locked()`.
- `stage2_try_break_pte()` on a table entry: invalidates with
  `kvm_tlb_flush_vmid_range()` over the span of that entry; the whole VMID is
  flushed only when `system_supports_tlb_range()` is false.
- `stage2_attr_walker()`: returns `-EAGAIN` for any invalid entry, so a walker
  that meets another walker's locked entry fails before it tries `cmpxchg()`.
