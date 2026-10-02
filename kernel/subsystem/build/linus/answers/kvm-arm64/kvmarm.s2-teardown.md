- `kvm_free_stage2_pgd()` on a shadow: calls `kvm_init_nested_s2_mmu()` while
  it still holds the write lock, whether or not `pgt` was set.
- `kvm_stage2_destroy()`: runs without `kvm->mmu_lock`; it calls
  `stage2_destroy_range()`, which calls
  `KVM_PGT_FN(kvm_pgtable_stage2_destroy_range)` one
  `kvm_granule_size(KVM_PGTABLE_MIN_BLOCK_LEVEL)` at a time with
  `cond_resched()` between, then
  `KVM_PGT_FN(kvm_pgtable_stage2_destroy_pgd)`.
- Host teardown does not call `kvm_pgtable_stage2_destroy()`; only
  `kvm_guest_destroy_stage2()` at EL2 does.
- `stage2_apply_range()` on `mmu->pgt == NULL`: returns `-EINVAL` on the first
  chunk, 0 once it has dropped the lock; `__unmap_stage2_range()` warns on
  non-zero.
- `kvm_mmu_split_huge_pages()`: re-reads `kvm->arch.mmu.pgt` after it retakes
  the lock and returns `-EINVAL` if it is NULL.
- Fault paths: `kvm_s2_fault_map()`, `gmem_abort()`, `pkvm_mem_abort()` and
  `handle_access_fault()` do not test `pgt` for NULL.
- Callers of `kvm_free_stage2_pgd()`: `kvm_uninit_stage2_mmu()`,
  `kvm_arch_flush_shadow_all()` (reached from `kvm_mmu_notifier_release()`),
  and the error path of `kvm_vcpu_init_nested()` on MMUs not yet published.
