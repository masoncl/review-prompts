- Models take `add_hugetlb_folio()` to drop the caller's reference. A free
  hugetlb folio in the pool has refcount 0; `folio_ref_unfreeze()` sets it to
  1 when the folio is handed out, for example in
  `dequeue_hugetlb_folio_node_exact()`.
- Models take the khugepaged limits to be scaled by a shift for orders below
  PMD order. `collapse_max_ptes_swap()` and `collapse_max_ptes_shared()` in
  `mm/khugepaged.c` return 0 below PMD order when `cc->is_khugepaged`.
- Models do not know `VM_UFFD_RWP`. A fault on a protnone huge PMD with the
  uffd bit in a `userfaultfd_rwp()` VMA goes to `do_huge_pmd_uffd_rwp()`;
  `remove_migration_pmd()` puts `PAGE_NONE` back when `pmd_swp_uffd()` and
  `userfaultfd_rwp()` both hold; `userfaultfd_protected()` covers both modes.
- Models take a pfn that is not memory to give `-ENXIO` from
  `memory_failure()`. A pfn for which `pfn_valid()` and
  `arch_is_platform_page()` are both false goes to `memory_failure_pfn()`,
  which signals the tasks collected through ranges registered with
  `register_pfn_address_space()` and returns what `action_result()` returns.
- Models take the huge zero folio to be refcounted. `set_huge_zero_folio()`
  in `mm/huge_memory.c` marks its PMD with `pmd_mkspecial()`.
- Models take a tail page to hold a pointer to its head.
  `compound_info_has_mask()` in `include/linux/page-flags.h` is true only
  with `CONFIG_HUGETLB_PAGE_OPTIMIZE_VMEMMAP` and a power-of-two
  `struct page`, and `set_compound_head()` takes the order.
- Models decode non-present PTEs with is_swap_pte(), pte_to_swp_entry() and
  is_migration_entry(). None is defined in this tree; code uses
  `softleaf_from_pte()` and tests such as `softleaf_is_migration()` in
  `include/linux/leafops.h`.
- Models write the uffd-wp bit helpers with a _wp suffix. Here the PTE and
  hugetlb tests are `pte_uffd()` and `huge_pte_uffd()`; `userfaultfd_wp()`
  and `vmf_orig_pte_uffd_wp()` keep their names.
- Models look for `lru_add_drain()` in mm/swap.c. That file is not in this
  tree; it is in `mm/folio.c`.
