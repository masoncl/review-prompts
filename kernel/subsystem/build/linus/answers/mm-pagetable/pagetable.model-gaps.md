- Models take GUP on a protnone entry to depend on `FOLL_HONOR_NUMA_FAULT`
  only. `gup_can_follow_protnone()` in `include/linux/mm.h` returns false first
  for an accessible `VM_UFFD_RWP` VMA.
- Models do not know `sync_with_folio_pmd_zap()` in `mm/internal.h`: a folio
  unmap that finds `pmd_none()` without the lock takes and drops the PMD lock,
  so a concurrent `zap_huge_pmd()` has removed the rmap. `zap_pmd_range()` and
  `page_vma_mapped_walk()` call it.
- Models write the uffd support test as pgtable_supports_uffd_wp(). The test
  for marker support here is `uffd_supports_wp_marker()` in
  `include/asm-generic/pgtable_uffd.h`.
- Models test VMA flags only as `vma->vm_flags & VM_WRITE`, and COW with
  is_cow_mapping(). `struct vm_area_struct` holds a union of `vm_flags` and the
  bitmap `flags`; `vma_test()` and `vma_test_any_mask()` are the same tests,
  and COW is `vma_is_cow_mapping()`.
- Models raise the swap count at unmap with swap_duplicate(). Here
  `ttu_anon_swapbacked_folio()` in `mm/rmap.c` calls `folio_dup_swap()`.
- Models take `folio_referenced_one()` to clear young one PTE at a time. It
  calls `clear_flush_young_ptes_notify()`, or `lru_gen_look_around()` under
  MGLRU, on a `folio_pte_batch()` run.
- Models do not know `ptep_try_set()` in `include/linux/pgtable.h`: an atomic
  install into an empty PTE; `flush_tlb_before_set()` is the flush made after
  a populated entry is cleared, before the retry. Both are called only from
  `kernel/bpf/arena.c`, for kernel tables. The generic `ptep_try_set()`
  returns false; x86 overrides it, arm64 only under `CONFIG_ARM64_CONTPTE`.
- Models take `remap_pfn_range()` to be the only way to map PFNs at mmap time.
  A `mmap_prepare` hook gets a `struct vm_area_desc` and no VMA;
  `remap_pfn_range_complete()` in `mm/memory.c` maps once the VMA exists.
- Models do not know that `try_to_unmap()` sends hugetlb folios to
  `try_to_unmap_poisoned_hugetlb_one()` and not to `try_to_unmap_one()`.
