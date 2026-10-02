- `collapse_huge_page()` entry: mmap_lock is not held. `collapse_scan_pmd()`
  calls `mmap_read_unlock()` before `mthp_collapse()` and sets `*lock_dropped`.
- mmap_lock after the swap-in stage: held for write until `out_up_write`; it is
  not downgraded.
- Write stage order: `hugepage_vma_revalidate()`, `vma_start_write()`,
  `check_pmd_still_valid()`, `anon_vma_lock_write()`.
- anon_vma write lock: released after isolation only for PMD order; for a
  smaller order it is held until `out_up_write`.
- `hugepage_vma_revalidate()`: checks `collapse_test_exit_or_disable()`, then
  `thp_vma_suitable_order()` with `PMD_ORDER` whatever the target order, then
  `thp_vma_allowable_orders()` for the target order, then, when `expect_anon`
  is true, `vma->anon_vma` and `vma_is_anonymous()`.
- `hugepage_vma_revalidate()` lookup: uses `find_vma()`, which can return a VMA
  above the address; the suitability test is what rejects it.
- `check_pmd_still_valid()`: compares the `pmd_t *` pointer from a new walk and
  the entry state; it does not compare the entry value with an earlier one.
- `__collapse_huge_page_swapin()`: called only when `unmapped` is nonzero.
- PTE lock for isolation: taken by `pte_offset_map_lock()` on the stack copy
  `_pmd`, since the real PMD is clear; dropped with `spin_unlock()` while the
  table stays mapped until `out_up_write`.
- `__collapse_huge_page_copy()`: holds no page table lock for the copy;
  `__collapse_huge_page_copy_succeeded()` takes the PTE lock per entry to clear
  it.
- Install below PMD order: PMD lock plus PTE lock nested inside; PMD order
  takes the PMD lock only.
