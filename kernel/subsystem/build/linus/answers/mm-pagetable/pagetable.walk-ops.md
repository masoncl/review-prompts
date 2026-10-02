- `pud_entry`, `pmd_entry`: called for every entry that is not `pud_none()` /
  `pmd_none()`, so also for leaf entries and for non-present ones (migration,
  device-private).
- `pte_hole` at PUD and PMD level: called for none entries only; a
  non-present entry is not a hole.
- `pgd_entry`, `p4d_entry`: the test is `pgd_none_or_clear_bad()` /
  `p4d_none_or_clear_bad()`; a bad entry is cleared and handled as a hole.
- None PMD in a walk without `install_pte`: gets `pte_hole` if set, and
  `pmd_entry` is not called for it.
- `depth`: takes only -1, 0, 1, 2, 3. There is no value for the PTE level;
  none PTEs go to `pte_entry`, or to `install_pte` when that is set.
- `depth` -1: a gap before or after a VMA, a `VM_PFNMAP` VMA skipped by the
  default test, and a hugetlb range where `hugetlb_walk()` returns NULL.
- `real_depth()` in `mm/pagewalk.c`: a hole found at a folded level is
  reported at the nearest level above that is not folded, for example 0 from
  `walk_p4d_range()` when `PTRS_PER_P4D == 1`.
- Huge PMD that `pmd_entry` already handled: the walker cannot tell; in a VMA
  walk with `pte_entry` set it still splits and descends unless the callback
  set `ACTION_CONTINUE`.
- After the split the walker goes straight to `walk_pte_range()`; it retries
  the PMD only if the PTE table cannot be mapped.
- `walk_pmd_range()` re-reads the PUD before it touches any PMD: if the PUD is
  not present or is a leaf it sets `ACTION_AGAIN` and returns 0.
- `walk_pud_range()` then retries that PUD, so `pud_entry` can run more than
  once for one PUD.
- `post_vma`: runs whenever `pre_vma` returned 0, including after a walk that
  returned non-zero; see `__walk_page_range()`.
- `pre_vma` and `post_vma` also run for a hugetlb VMA when no `hugetlb_entry`
  is set.
