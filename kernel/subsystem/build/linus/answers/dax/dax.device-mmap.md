- Shared-mapping test: `__check_vma()` tests `VMA_MAYSHARE_BIT` with
  `vma_flags_test_any()`, not `VM_SHARED`.
- Fourth check: `__check_vma()` returns `-EINVAL` when `file_is_dax()` is
  false for the file; it does not call `vma_is_dax()`.
- mmap hook: there is no dax_mmap() here; `dax_mmap_prepare()` works on a
  `struct vm_area_desc`, calls `__check_vma()` under `dax_read_lock()` and
  sets `VMA_HUGEPAGE_BIT` with `vma_desc_set_flags()`.
- `check_vma()`: a wrapper that feeds a VMA to `__check_vma()`; each of
  `__dev_dax_pte_fault()`, `__dev_dax_pmd_fault()` and the real
  `__dev_dax_pud_fault()` calls it first and turns any error into
  `VM_FAULT_SIGBUS`.
- Order other than 0, `PMD_ORDER` or `PUD_ORDER`: `dev_dax_huge_fault()`
  returns `VM_FAULT_SIGBUS`, not `VM_FAULT_FALLBACK`.
- PMD or PUD range not fully inside the VMA: `VM_FAULT_SIGBUS`, not
  `VM_FAULT_FALLBACK`.
- Stub returning `VM_FAULT_FALLBACK`: only `__dev_dax_pud_fault()` without
  `CONFIG_HAVE_ARCH_TRANSPARENT_HUGEPAGE_PUD`; `__dev_dax_pmd_fault()` has no
  stub.
- `dax_set_mapping()`: writes `folio->mapping` and `folio->index` and nothing
  else; it does not touch the folio order.
- `dax_set_mapping()` with `dev_dax->pgmap->vmemmap_shift` set: writes only
  the head folio; `dev_dax_probe()` sets `vmemmap_shift` whenever
  `dev_dax->align` is larger than `PAGE_SIZE`.
- Inserts: `vmf_insert_page_mkwrite()`, `vmf_insert_folio_pmd()` and
  `vmf_insert_folio_pud()`; `drivers/dax/device.c` inserts no raw pfn.
