- `KVM_PGT_FN(fn)`: defined in `arch/arm64/kvm/mmu.c` and used only there;
  expands to `fn`, or to `p ## fn` when `is_protected_kvm_enabled()`.
- `struct kvm_pgtable` under pKVM: `pkvm_mappings` shares a union with
  `ia_bits`, `start_level`, `pgd`, `mm_ops`, `flags` and `force_pte_cb`;
  besides `pkvm_mappings` only `mmu` is usable.
- `kvm_stage2_destroy()` takes the range from `pgt->mmu->vtcr`, not from
  `pgt->ia_bits`, for that reason.
- `kvm_init_stage2_mmu()` under pKVM: returns before it sets
  `mmu->last_vcpu_ran` and `mmu->pgd_phys`.
- pKVM variants ignore the `mm_ops` and walk-flag arguments.
- `struct kvm_pgtable_mm_ops` has no member named `fault_cache`.
- Callbacks the stage-2 code tests for NULL before calling:
  `dcache_clean_inval_poc` and `icache_inval_pou`; `kvm_pgtable_hyp_unmap()`
  tests `page_count`. The others are called unconditionally.
- `page_count`: the library reads a result of 1 as "this table holds no
  counted entry" (`stage2_unmap_walker()`, `stage2_free_table_post()`,
  `kvm_pgtable_stage2_free_unlinked()`), so nothing else may hold a
  reference on a table page.
