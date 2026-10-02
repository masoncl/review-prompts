- `file_thp_enabled()` tests, in order: `vma->vm_file` set; not
  `IS_ANON_FILE()`; `mapping_pmd_folio_support()` on the mapping;
  `S_ISREG()`.
- Not tested: `inode_is_open_for_write()`, `VM_EXEC`, any config symbol.
- CONFIG_READ_ONLY_THP_FOR_FS, filemap_nr_thps_inc() and filemap_nr_thps():
  not in this tree. Opening a file for write does not drop its page cache, and
  `collapse_file()` has no writer recheck.
- `mapping_pmd_folio_support()` in `include/linux/pagemap.h`: true when
  `mapping_min_folio_order()` <= `PMD_ORDER` <= `mapping_max_folio_order()`. A
  non-shmem filesystem that has not set a folio order range reaching
  `PMD_ORDER` is never collapsed.
- Eligible regular files include files open for writing and writable
  mappings.
- `vma_can_map_huge_file()` in `mm/huge_memory.c`: runs
  `vma_file_check_thp_tuneables()` before `file_thp_enabled()`. The daemon needs
  `hugepage_global_always()`, or `hugepage_global_enabled()` with
  `VM_HUGEPAGE`; `TVA_FORCED_COLLAPSE` skips that test.
- Dirty or writeback folio of a non-shmem file: `collapse_file()` fails with
  `SCAN_PAGE_DIRTY_OR_WRITEBACK`; it calls `filemap_flush()` only when the inode
  is not open for write.
- MADV_COLLAPSE on that result: `collapse_single_pmd()` calls
  `filemap_write_and_wait_range()` and retries once, when
  `mapping_can_writeback()`.
