- `vms_complete_munmap_vmas()`: calls `mmap_write_downgrade()` first when
  `vms->unlock` is set, so `free_pgtables()` then runs under the mmap read
  lock; otherwise under the write lock.
- After the downgrade no VMA is write-locked; `vma_mark_detached()` left
  `vm_refcnt` at zero, so `vma_start_read()` fails, and
  `do_vmi_align_munmap()` cleared the range from the tree before that.
- Call path: `vms_clear_ptes()` fills a `struct unmap_desc` (`mm/vma.h`) and
  calls `unmap_region()`, which calls `unmap_vmas()` then `free_pgtables()`.
- `free_pgtables(tlb, unmap)`: floor is `pg_start`; ceiling is the next VMA's
  `vm_start`, or `pg_end` after the last VMA; `vms_clear_ptes()` sets
  `pg_start` and `pg_end` from `vms->unmap_start` and `vms->unmap_end`.
- There is no hugetlb_free_pgd_range() and no unlink_file_vma() here;
  `free_pgtables()` calls `free_pgd_range()` for hugetlb VMAs too, and
  `unlink_file_vma_batch_add()` with `unlink_file_vma_batch_final()`.
- `mm_wr_locked`: `free_pgtables()` calls `vma_start_write()` only when it is
  true; `UNMAP_STATE()` sets it true, `unmap_all_init()` false, and
  `exit_mmap()` sets it after `mmap_write_lock()`.
- Attached VMAs reach `free_pgtables()` only with the mmap write lock held and
  `mm_wr_locked` true: in `exit_mmap()` and in the failure path of
  `dup_mmap()` in `mm/mmap.c`.
- `__mmap_new_file_vma()` error path: also uses `UNMAP_STATE()` under the
  write lock, on a new VMA that is not yet in the tree.
- `free_pgd_range()`: takes no page-table lock; `free_pte_range()` does
  `pmd_clear()` and `pte_free_tlb()` bare.
- RCU delay of the freed table: only with `CONFIG_MMU_GATHER_RCU_TABLE_FREE`;
  without `CONFIG_MMU_GATHER_TABLE_FREE`, `tlb_remove_table()` queues the
  table as an ordinary page.
- **Unsafe usage**: under the mmap read lock, walking user page tables at an
  address without first finding an attached VMA that covers it.
  - Unsafe: `vms_complete_munmap_vmas()` frees the tables of an unmapped
    range under the mmap read lock, and `free_pte_range()` takes no
    page-table lock.
  - Safe: under the mmap write lock, as `ptdump_walk_pgd()` does;
    `walk_page_range_debug()` asserts it.
  - Safe: after a VMA lookup under the lock, as
    `try_collapse_pte_mapped_thp()` does with `vma_lookup()` before
    `find_pmd_or_thp_or_none()`; the unmapped range has no VMA in the tree.
