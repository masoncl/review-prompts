- `walk_page_range()` without `test_walk`: `walk_page_test()` skips every
  `VM_PFNMAP` VMA; it is never walked, with or without `pte_hole`.
- Skipped `VM_PFNMAP` VMA in `walk_page_range()`: `pte_hole`, if set, is
  called once for the part of the VMA inside the range, with depth -1.
- `pte_hole` return on that path: negative aborts the walk; zero and positive
  both mean skip, so a positive value never reaches the caller there.
- Supplied `test_walk`: replaces the `VM_PFNMAP` check, so it has to reject
  `VM_PFNMAP` itself if it wants that, as `clear_refs_test_walk()` in
  `fs/proc/task_mmu.c` does.
- **Unsafe usage**: a `test_walk` that returns a positive value to skip one
  VMA, in ops passed to `walk_page_mapping()`.
  - Unsafe: `walk_page_mapping()` ends its loop over VMAs on a positive
    `test_walk` return and returns 0; the remaining VMAs of the mapping are
    not walked.
  - Safe: the same return in ops passed to `walk_page_range()`;
    `walk_page_range_mm_unsafe()` skips that VMA and continues with the next,
    as for `clear_refs_test_walk()` in `fs/proc/task_mmu.c`.
- `walk_page_vma()`, `walk_page_range_vma()` and
  `walk_page_range_vma_unsafe()`: do not call `walk_page_test()`, so they walk
  a `VM_PFNMAP` VMA.
- hugetlb VMA with no `hugetlb_entry`: no page table of it is walked and the
  result for it is 0.
