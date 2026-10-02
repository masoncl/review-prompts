- `tlb_gather_mmu_vma()` in `mm/mmu_gather.c`: `tlb_gather_mmu()` on
  `vma->vm_mm`, then `tlb_update_vma_flags()`, then for a hugetlb VMA
  `tlb_change_page_size()` to the hstate size.
- `tlb_gather_mmu_vma()`: records no range and does not call
  `flush_cache_range()`; its callers call `flush_cache_range()` themselves
  and need no `tlb_start_vma()`.
- `tlb_gather_mmu_vma()` callers: all are hugetlb paths that may unshare a
  PMD table, in `mm/hugetlb.c` and `mm/rmap.c`.
- After `huge_pmd_unshare()`: the caller must call
  `huge_pmd_unshare_flush()` while still holding `i_mmap_rwsem` for write
  (it asserts that), and before `tlb_finish_mmu()`.
- `tlb_gather_mmu_fullmm()`: used by `exit_mmap()` and by
  `free_ldt_pgtables()` in `arch/x86/kernel/ldt.c`; with `fullmm` the x86
  `tlb_flush()` ignores the tracked range.
- `fullmm`: makes `tlb_start_vma()`, `tlb_end_vma()` and `tlb_free_vmas()`
  return at once.
- `tlb_gather_mmu()` followed by `zap_vma_range_batched()`: notifier and
  `update_hiwater_rss()` are done for the caller; followed by
  `unmap_vmas()`: only the notifier is.
