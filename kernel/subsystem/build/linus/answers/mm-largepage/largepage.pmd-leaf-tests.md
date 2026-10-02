| Test | True for | Easy to miss |
|---|---|---|
| `pmd_trans_huge()` | present huge PMD, also one made invalid by `pmdp_invalidate()` | also true for a hugetlb PMD: x86 tests only `_PAGE_PSE`; riscv and s390 return `pmd_leaf()` |
| `pmd_leaf()` | arch leaf test | some architectures do not test present, for example x86, loongarch and powerpc book3s64 |
| `pmd_is_huge()` | present and `pmd_trans_huge()`, or any non-none non-present PMD | does not check the entry kind |

- `pmd_is_huge()`: defined in `include/linux/huge_mm.h`; constant false without
  `CONFIG_TRANSPARENT_HUGEPAGE`.
- `pmd_is_valid_softleaf()`: the test that a non-present PMD is a migration or
  device-private entry; `pmd_is_huge()` does not make it.
- `pmd_leaf()` on powerpc book3s64: true for a PMD softleaf entry, because
  `__swp_entry_to_pte()` sets `_PAGE_PTE`.
- `pmd_leaf()`: paired with a `pmd_present()` test where the PMD may be
  non-present, for example in `mm/pagewalk.c` and `mm/mremap.c`.
- `pmd_is_huge()` is the lockless gate in generic range walkers, for example
  `zap_pmd_range()` and `change_pmd_range()`; search for the rest.
- `pmd_trans_huge()` is used where only a present entry is wanted, for example
  `__handle_mm_fault()` after its `pmd_present()` test, and `__pte_offset_map()`.
- hugetlb: excluded by the VMA, not by any of the three tests.
- `vma_is_special_huge()`: static in `mm/huge_memory.c` and false for a DAX VMA;
  code elsewhere uses `vm_normal_folio_pmd()`.
- **Potentially unsafe usage**: taking a true `pmd_trans_huge()` or
  `pmd_is_huge()` to mean "maps a THP folio".
  - Unsafe: when the VMA may be hugetlb, DAX or PFN-mapped, or the entry may be
    the huge zero folio or non-present; `vm_normal_folio_pmd()` returns NULL
    for special and huge zero entries and reads `pmd_pfn()` of what it is given.
  - Safe: `madvise_free_huge_pmd()`: `mm/madvise.c` refuses `MADV_FREE` on a
    non-anonymous VMA, and under `pmd_trans_huge_lock()` it tests
    `is_huge_zero_pmd()` and `pmd_present()` before `pmd_folio()`.
  - Safe: `do_huge_pmd_numa_page()`: `pmd_same()` under `pmd_lock()`, then
    `vm_normal_folio_pmd()` and a NULL test.
