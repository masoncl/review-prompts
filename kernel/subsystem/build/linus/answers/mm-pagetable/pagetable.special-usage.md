- `insert_pmd()` folio path: takes the reference with `folio_get()`, the
  rmap with `folio_add_file_rmap_pmd()`, and the counter with
  `add_mm_counter()`.
- `insert_pmd()` with the huge zero folio: `folio_mk_pmd()` then
  `pmd_mkspecial()`, and no reference, rmap or counter. `insert_pud()` has
  no such branch.
- `insert_page_into_pte_locked()` with a zero folio: `mk_pte()` then
  `pte_mkspecial()`, and no reference, rmap or counter.
- `insert_pmd()` and `insert_pud()`: the `prot` argument is used only on the
  PFN path; the folio path uses `vma->vm_page_prot`.
- `folio_mk_pmd()` is `pmd_mkhuge(pfn_pmd())`; `folio_mk_pud()` is
  `pud_mkhuge(pfn_pud())`; see `include/linux/mm.h`.
- `pmd_mkspecial()` and `pud_mkspecial()`: return the entry unchanged
  without `CONFIG_ARCH_SUPPORTS_PMD_PFNMAP` and
  `CONFIG_ARCH_SUPPORTS_PUD_PFNMAP`; `pmd_special()` and `pud_special()` are
  then constant false.
- The three `BUG_ON()`s shared by `vmf_insert_pfn_pmd()`,
  `vmf_insert_pfn_pud()` and `vmf_insert_pfn_prot()`: in a `VM_PFNMAP` VMA
  they keep a raw PFN recognisable by the VMA rules of `__vm_normal_page()`
  at a level with no special bit.
- **Unsafe usage**: `pmd_mkspecial()`, `pud_mkspecial()` or `pte_mkspecial()`
  on an entry for which a reference, an rmap or an mm counter was taken.
  `zap_huge_pmd()` gets NULL from `vm_normal_folio_pmd()` and drops none of
  them.
  - Safe: special on a folio-built entry only for the zero folios, with no
    reference, rmap or counter taken for the entry, as
    `set_huge_zero_folio()` does.
- **Potentially unsafe usage**: a special entry in a VMA with neither
  `VM_PFNMAP` nor `VM_MIXEDMAP`.
  - Unsafe: for any PFN other than the zero PFNs, when the VMA has no
    `find_normal_page`; `__vm_normal_page()` calls `print_bad_page_map()`,
    which taints the kernel.
  - Safe: the zero PFN or the huge zero folio, as `do_anonymous_page()` and
    `set_huge_zero_folio()` do; `__vm_normal_page()` tests `is_zero_pfn()`
    and `is_huge_zero_pfn()`.
- **Potentially unsafe usage**: a raw-PFN entry, with no reference taken, for
  a `pfn_valid()` PFN in a `VM_MIXEDMAP` VMA.
  - Unsafe: at a level with no special bit, for a PFN other than the zero
    PFNs; `__vm_normal_page()` returns the page as normal and zap drops a
    reference and an rmap nobody took.
  - Safe: at a level with a special bit, through `insert_pfn()`, which sets
    `pte_mkspecial()`; `__vm_normal_page()` returns NULL for a special entry
    in a `VM_MIXEDMAP` VMA that has no `find_normal_page`.
  - Safe: without a PTE special bit, inserting the page refcounted, as
    `__vm_insert_mixed()` does with `insert_page()`;
    `vmf_insert_pfn_prot()` has a `BUG_ON()` for this case.
- **Potentially unsafe usage**: using `pmd_special()` or `pud_special()`
  alone to find PFN maps.
  - Unsafe: when a leaf that the test misses is then used as a refcounted
    folio; the test is constant false where the level has no special bit.
  - Safe: `copy_huge_pmd()`; a PFN leaf it misses is in a VMA with `vm_ops`,
    and it returns 0 for a VMA that fails `vma_is_anonymous()` before it
    touches the page.
  - Safe: `vm_normal_page_pmd()`, `vm_normal_folio_pmd()` or
    `vm_normal_page_pud()`, which fall back to the VMA rules.
