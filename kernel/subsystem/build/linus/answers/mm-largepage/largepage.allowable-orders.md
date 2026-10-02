- `enum tva_type` in `include/linux/huge_mm.h`: four values, `TVA_SMAPS`,
  `TVA_PAGEFAULT`, `TVA_KHUGEPAGED`, `TVA_FORCED_COLLAPSE`; the `type`
  argument is one of them, not a mask of flags.
- DAX and PFN/MIXEDMAP mask: `THP_ORDERS_ALL_SPECIAL_DAX`; there is no
  THP_ORDERS_ALL_SPECIAL or THP_ORDERS_ALL_FILE_DAX here.
- `vma_is_special_huge()`: static in `mm/huge_memory.c`, returns false for a
  DAX VMA and true for any other VMA with `VMA_PFNMAP_BIT` or
  `VMA_MIXEDMAP_BIT`; `__thp_vma_allowable_orders()` tests `vma_is_dax()`
  beside it.
- Anonymous orders: `THP_ORDERS_ALL_ANON` is 2 to `PMD_ORDER`; order 1 is never
  returned.
- File orders: `THP_ORDERS_ALL_FILE_DEFAULT` is 1 to `MAX_PAGECACHE_ORDER`; the
  function does not narrow a non-shmem file VMA to PMD order.
- `VM_NO_KHUGEPAGED` test: applies only to `TVA_KHUGEPAGED` and
  `TVA_FORCED_COLLAPSE`; a page fault or smaps query on such a VMA is not
  rejected by it.
- Process-wide disable: `vma_thp_disabled()` tests
  `MMF_DISABLE_THP_COMPLETELY` (the result is always 0) and
  `MMF_DISABLE_THP_EXCEPT_ADVISED` (ignored with `VM_HUGEPAGE` or forced
  collapse); there is no MMF_DISABLE_THP.
- File VMA and the global setting: `vma_can_map_huge_file()` in
  `mm/huge_memory.c` requires `hugepage_global_always()`, or `VM_HUGEPAGE` with
  `hugepage_global_enabled()`.
- Global setting bypassed: for `TVA_FORCED_COLLAPSE`, and for a
  `VMA_PFNMAP_BIT` VMA whose `vm_ops` has `->huge_fault`; see
  `vma_file_bypass_thp_tuneables()`.
- DAX VMA: returns before `vma_can_map_huge_file()`, so a DAX page fault gets
  its orders whatever the global setting is.
- `file_thp_enabled()` (collapse and smaps): needs `vm_file`, a regular file,
  not `IS_ANON_FILE()`, and `mapping_pmd_folio_support()`; there is no
  CONFIG_READ_ONLY_THP_FOR_FS in this tree.
