- pte_folio(): not in this tree.
- `pmd_folio()`: a macro in `include/linux/pgtable.h`,
  `page_folio(pmd_page(pmd))`; it makes no check of its own.
- **Potentially unsafe usage**: `pmd_folio()` on a PMD once
  `pmd_trans_huge_lock()` has returned the lock.
  - Unsafe: when nothing tests presence afterwards; `pmd_is_huge()` in
    `include/linux/huge_mm.h` is true for every non-empty non-present PMD, so
    the lock is also returned for migration and device-private entries.
  - Safe: test `pmd_present()` under the lock first, as
    `madvise_free_huge_pmd()` in `mm/huge_memory.c` does.
- `pmd_to_softleaf_folio()`: in `include/linux/leafops.h`; returns NULL after
  `VM_WARN_ON_ONCE()` unless the entry is migration or device-private, so the
  caller must handle NULL.
- `pmd_to_softleaf_folio()` without `CONFIG_ARCH_HAS_PMD_SOFTLEAVES`: always
  NULL.
- `pmd_to_softleaf_folio()` callers: only `normal_or_softleaf_folio_pmd()` in
  `mm/huge_memory.c`, for `zap_huge_pmd()`; other PMD code, for example
  `change_non_present_huge_pmd()`, uses
  `softleaf_to_folio(softleaf_from_pmd(pmd))`.
