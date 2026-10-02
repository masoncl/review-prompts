- `kvm_fault_lock()` in `arch/arm64/include/asm/kvm_mmu.h`: write lock when
  `is_protected_kvm_enabled()`, read lock otherwise; it tests nothing else
  (not the fault type, not nested).
- Callers of `kvm_fault_lock()`: `kvm_s2_fault_map()` (the tail of
  `user_mem_abort()`) and `gmem_abort()`.
- `pkvm_mem_abort()`, used when `kvm_vm_is_protected()`: takes plain
  `write_lock()`.
- `handle_access_fault()`: plain `read_lock()`, also under pKVM.
- Aging from the notifier: write lock, taken by `kvm_handle_hva_range()`;
  `arch/arm64/kvm/Kconfig` does not select `CONFIG_KVM_MMU_LOCKLESS_AGING`.
- Protected VM: `kvm_unmap_gfn_range()`, `kvm_age_gfn()`,
  `kvm_test_age_gfn()` and `kvm_stage2_unmap_range()` return before touching
  anything.
- Splitting under pKVM: `kvm_mmu_split_huge_pages()` returns 0 before it
  reaches `pkvm_pgtable_stage2_split()`, because `split_page_chunk_size`
  stays 0; `kvm_pkvm_ext_allowed()` rejects
  `KVM_CAP_ARM_EAGER_SPLIT_CHUNK_SIZE`.
- **Potentially unsafe usage**: calling a `KVM_PGT_FN()` target under pKVM
  with `kvm->mmu_lock` held for read.
  - Unsafe: when the target inserts into or removes from
    `pgt->pkvm_mappings`; `pkvm_pgtable_stage2_map()` and
    `pkvm_pgtable_stage2_unmap()` have `lockdep_assert_held_write()`.
  - Safe: `pkvm_pgtable_stage2_mkyoung()` under the read lock, as
    `handle_access_fault()` does; it only issues a hypercall and does not
    touch `pgt->pkvm_mappings`.
