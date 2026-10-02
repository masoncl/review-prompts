- PUD forms: only `folio_add_file_rmap_pud()` and `folio_remove_rmap_pud()`.
  There is no PUD dup function, file or anon, and no anon PUD add.
- `folio_dup_file_rmap_pmd()`: has no caller; `copy_huge_pmd()` returns 0
  for a non-anonymous VMA, unless the PMD is present, `pmd_special()` and not
  the huge zero PMD, and leaves the PMD to be refilled on fault.
- hugetlb file mapping at fork: `hugetlb_add_file_rmap()`; there is no
  hugetlb_dup_file_rmap().
- `folio_add_new_anon_rmap()`: picks the accounting from the folio size, not
  from a level argument. A folio for which `folio_test_pmd_mappable()` is true
  is counted as one entire mapping, so the caller must map it with a PMD.
- PMD forms without `CONFIG_TRANSPARENT_HUGEPAGE`: `WARN_ON_ONCE(true)` and no
  accounting; `folio_try_dup_anon_rmap_pmd()` returns `-EBUSY`.
- PUD forms: also need `CONFIG_HAVE_ARCH_TRANSPARENT_HUGEPAGE_PUD`, else the
  same stub.
- `__folio_rmap_sanity_checks()`: every check is `VM_WARN_ON_FOLIO()` or
  `VM_WARN_ON_ONCE()`, so a wrong level or a hugetlb folio passes silently
  without `CONFIG_DEBUG_VM`.
