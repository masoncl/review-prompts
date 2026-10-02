- Non-present PMD that is not none: it is a huge software leaf entry
  (migration, device-private).
- `pmd_trans_huge_lock()`: tests `pmd_is_huge()` in
  `include/linux/huge_mm.h`, which is true for a present `pmd_trans_huge()`
  PMD and for any non-present non-none PMD.
- Under that lock the callback tests `pmd_present()` before `pmd_folio()`, as
  `mlock_pte_range()` in `mm/mlock.c` does.
- Failed mapping of the PTE table: the callback either sets `ACTION_AGAIN` and
  returns 0, as `smaps_pte_range()` does, or returns 0 and skips the range, as
  `damon_mkold_pmd_entry()` in `mm/damon/vaddr.c` does.
- `split_huge_pmd()` in the walker: tests `pmd_is_huge()`, so it splits
  non-present huge entries as well as present ones.
- Without `CONFIG_TRANSPARENT_HUGEPAGE`: `split_huge_pmd()` is an empty macro
  and `pmd_trans_huge_lock()` returns NULL.
- No-VMA walk: `walk->vma` is NULL and `__pmd_trans_huge_lock()` dereferences
  it, so the callback tests `pmd_leaf()` itself, as `vmemmap_pmd_entry()` in
  `mm/hugetlb_vmemmap.c` does.
