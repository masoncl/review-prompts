- There is no find_special_page() here; the hook is `find_normal_page` in
  `struct vm_operations_struct`, under `CONFIG_FIND_NORMAL_PAGE`.
- `find_normal_page`: called only for a special entry at a level that has a
  special bit; it runs before the VMA flag tests and its result is returned
  as is.
- `__vm_normal_page()`: does not limit `find_normal_page` to PTEs; that it
  is used for PTEs only is a property of the one implementor,
  `gntdev_vma_find_normal_page()` in `drivers/xen/gntdev.c`.
- `pgtable_level_has_pxx_special()` in `mm/memory.c`: decides per level.
  PTE uses `CONFIG_ARCH_HAS_PTE_SPECIAL`, PMD
  `CONFIG_ARCH_SUPPORTS_PMD_PFNMAP`, PUD `CONFIG_ARCH_SUPPORTS_PUD_PFNMAP`.
- Architecture with a PTE special bit and no
  `CONFIG_ARCH_SUPPORTS_PMD_PFNMAP`: `vm_normal_page_pmd()` uses the VMA
  flag rules, with `linear_page_index()` of the PMD address.
- VMA flag rules, order: `VM_MIXEDMAP` is tested first and uses only
  `pfn_valid()`; the `vm_pgoff` compare and `vma_is_cow_mapping()` apply to
  `VM_PFNMAP` without `VM_MIXEDMAP`.
- Zero PFN and huge zero PFN at a level with a special bit: recognised only
  through the special bit. A non-special entry with such a PFN reaches
  `VM_WARN_ON_ONCE()` and is returned as a normal page.
