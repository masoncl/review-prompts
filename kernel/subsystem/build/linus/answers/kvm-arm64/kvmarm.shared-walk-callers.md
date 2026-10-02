- There is no KVM_PGTABLE_WALK_HANDLE_FAULT here. `kvm_pgtable_walk_continue()`
  in `arch/arm64/kvm/hyp/pgtable.c`: `-EAGAIN` ends the walk and is returned,
  unless the walker has `KVM_PGTABLE_WALK_IGNORE_EAGAIN`.
- Callers that pass `KVM_PGTABLE_WALK_SHARED`: `kvm_s2_fault_map()`,
  `gmem_abort()` and `handle_access_fault()` in `arch/arm64/kvm/mmu.c`; none
  of them passes `KVM_PGTABLE_WALK_IGNORE_EAGAIN`.
- `-EAGAIN` becomes 0 in `kvm_s2_fault_map()` and `gmem_abort()`, not in
  `user_mem_abort()` or `kvm_handle_guest_abort()`;
  `kvm_handle_guest_abort()` then turns 0 into 1 and the guest is re-entered.
- `kvm_s2_fault_map()` and `gmem_abort()`: set `ret` to the same `-EAGAIN`
  when `mmu_invalidate_retry()` fires, so the conversion covers both cases.
