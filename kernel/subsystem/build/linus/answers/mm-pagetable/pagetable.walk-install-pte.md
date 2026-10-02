- Entry points that accept `install_pte`: `walk_page_range_mm_unsafe()` and
  `walk_page_range_vma_unsafe()`, defined in `mm/pagewalk.c` and declared in
  `mm/internal.h`.
- There is no walk_page_range_mm() and no check_ops_valid() here; the check is
  `check_ops_safe()`.
- Every entry point declared in `include/linux/pagewalk.h` that takes a
  `struct mm_walk_ops`, and `walk_page_range_debug()`, reaches
  `check_ops_safe()` and returns `-EINVAL` when `install_pte` is set. That
  includes `walk_page_range()` and `walk_page_range_vma()`.
- hugetlb VMA with `install_pte`: `__walk_page_range()` returns `-EINVAL`
  before `pre_vma` runs.
- None entry at each level: `__p4d_alloc()`, `__pud_alloc()`, `__pmd_alloc()`
  or `__pte_alloc()` runs in place of `pte_hole`; a non-zero return ends the
  walk and is returned.
- After the allocation the entry callback of that level runs on the new entry,
  so `pud_entry` and `pmd_entry` see entries they would not see in a plain
  walk.
- `install_pte` without `pte_entry`: a present `pmd_trans_huge()` PMD is
  skipped, not split, and nothing is installed under it; a present
  `pud_trans_huge()` PUD likewise, when `pmd_entry` is unset too.
- `install_pte` with `pte_entry`: huge entries are split as in any VMA walk.
- **Unsafe usage**: supplying `install_pte` without `pte_entry`.
  - Unsafe: `walk_pte_range_inner()` calls `ops->pte_entry` with no NULL test
    for every PTE that is not `pte_none()`.
  - Safe: supply both, as `madvise_guard_install()` in `mm/madvise.c` does.
