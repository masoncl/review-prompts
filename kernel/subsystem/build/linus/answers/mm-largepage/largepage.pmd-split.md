- `__split_huge_pmd_locked()`: does not test whether the PMD is huge, only
  `VM_WARN_ON_ONCE()`; its one caller `split_huge_pmd_locked()` decides.
- `split_huge_pmd_locked()`: splits when `pmd_trans_huge()` or
  `pmd_is_valid_softleaf()`; this is narrower than `pmd_is_huge()`, which
  `split_huge_pmd()` tests locklessly.
- `split_huge_pmd_locked()` and `__split_huge_pmd()`: four arguments, no folio
  argument.
- `split_huge_pmd_address()`: does nothing when `mm_find_pmd()` returns NULL.
- Non-anonymous VMA, by entry, after the PMD is cleared and, when
  `arch_needs_pgtable_deposit()`, the deposited table is freed:

| Entry | Further work |
|---|---|
| `vma_is_special_huge()` VMA | none |
| migration entry | file RSS counter reduced only; no rmap removal, no `folio_put()` |
| huge zero PMD | none |
| present folio, DAX included | dirty and referenced moved, `folio_remove_rmap_pmd()`, counter, `folio_put()` |

- There is no devmap test here; `vma_is_special_huge()` is PFN-map or mixed-map
  and not DAX.
- Device-private PMD: device-private PTE entries without `freeze`, migration
  PTE entries with `freeze`.
- uffd bit: read with `pmd_uffd()` or `pmd_swp_uffd()`, written with
  `pte_mkuffd()` or `pte_swp_mkuffd()`.
- `userfaultfd_rwp()` VMA with the uffd bit set: the present PTEs are remade
  with `PAGE_NONE`; no other protnone state is carried.
