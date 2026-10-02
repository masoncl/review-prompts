- `/dev/zero` in `drivers/char/mem.c`: there is no mmap_zero() function and
  no success hook; `mmap_zero_prepare()` calls `vma_desc_set_anonymous()` for
  a private mapping, and `set_vma_user_defined_fields()` then calls
  `vma_set_anonymous()`.
- Default `vm_ops`: `vma_init()` and the desc in `__mmap_region()` both start
  with `&vma_dummy_vm_ops`; a hook gets an anonymous VMA only by storing
  NULL.
- Inside `__mmap_new_vma()`: a VMA for a file with `mmap_prepare` still has
  `vma_dummy_vm_ops`, so `vma_is_anonymous()` is false there even for
  private `/dev/zero`; it becomes true in `set_vma_user_defined_fields()`.
- `vma_link_file()`: tests only `vma->vm_file`, so a private `/dev/zero` VMA
  is in the file's `i_mmap` tree; `__mmap_complete()` calls `uprobe_mmap()`
  on it for the same reason.
- `vm_pgoff` of a private `/dev/zero` VMA as `__mmap_region()` creates it:
  the file offset passed to `mmap()`, not `vm_start >> PAGE_SHIFT`; the
  virtual offset is kept separately and read with `vma_start_anon_pgoff()`.
- **Potentially unsafe usage**: treating `vma_is_anonymous()` as "no file and
  `vm_pgoff` is the virtual page offset".
  - Unsafe: for a private `/dev/zero` VMA, where `vm_file` is set and
    `vma_start_pgoff()` returns a file offset.
  - Safe: test `vma_is_anonymous(vma) && !vma->vm_file`, as
    `assert_sane_pgoff()` in `mm/vma.h`, `linear_anon_page_index()` in
    `include/linux/pagemap.h` and `dontunmap_complete()` in `mm/mremap.c` do.
  - Safe: use `vma_start_anon_pgoff()` or `linear_anon_page_index()` for the
    anonymous offset.
- **Potentially unsafe usage**: dereferencing `vma->vm_file` after testing
  only `vma_is_anonymous()`.
  - Unsafe: when no earlier test rejected a VMA with a NULL `vm_file`; a
    non-anonymous VMA may have one, since `vma_is_anonymous()` reads only
    `vm_ops`; for example a VMA from `__install_special_mapping()`.
  - Safe: test `vma->vm_file` itself before the dereference, as
    `page_address_in_vma()` in `mm/rmap.c` does.
  - Safe: when the callers already rejected a non-anonymous VMA with no
    file, as `collapse_single_pmd()` in `mm/khugepaged.c`; its callers pass
    only a VMA that `__thp_vma_allowable_orders()` accepted, which for a
    non-anonymous VMA with `TVA_KHUGEPAGED` or `TVA_FORCED_COLLAPSE` requires
    `shmem_file()` or `file_thp_enabled()`, and both test `vm_file`.
