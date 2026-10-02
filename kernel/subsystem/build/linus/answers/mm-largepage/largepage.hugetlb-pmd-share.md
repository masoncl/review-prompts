- Sharer count: `pt_share_count`, an `atomic_t` in `struct ptdesc`, not the
  page refcount; 0 means not shared, see `ptdesc_pmd_is_shared()`.
- `huge_pmd_share()`: takes `i_mmap_lock_read()` itself and holds it until
  after `pmd_alloc()`.
- `hugetlb_fault()` as caller: holds the fault mutex and the hugetlb VMA lock
  for read, not `i_mmap_rwsem`.
- `want_pmd_share()` and `page_table_shareable()`: both require
  `vm_private_data` to be set.
- `page_table_shareable()`: compares `vm_flags` with `VM_LOCKED_MASK` masked
  out.
- `uffd_disable_huge_pmd_share()`: true for `VMA_UFFD_WP`, `VMA_UFFD_RWP` or
  `VMA_UFFD_MINOR`.
- There is no vma_shareable() here; the tests are inline in
  `want_pmd_share()`, built under `CONFIG_HUGETLB_PMD_PAGE_TABLE_SHARING`.
