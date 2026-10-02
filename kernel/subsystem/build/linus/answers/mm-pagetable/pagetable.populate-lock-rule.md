- Freeing, mmap lock mode: the write lock is not always held;
  `vms_complete_munmap_vmas()` in `mm/vma.c` downgrades to read first when
  `vms->unlock`, then frees.
- Why that is safe: `vms_gather_munmap_vmas()` already ran
  `vma_start_write()` and `vma_mark_detached()` on each VMA under the write
  lock.
- `free_pgtables()` and the VMA lock: calls `vma_start_write()` only when
  `unmap->mm_wr_locked` is set.
- `free_pgtables()` and rmap: it does not hold the rmap locks while freeing;
  it removes each VMA from rmap with `unlink_anon_vmas()` and the
  `unlink_file_vma_batch_add()` batch, then calls `free_pgd_range()`.
- Rmap lock only, installing: not allowed into a previously empty entry.
- Why: `unmap_region()` runs `unmap_vmas()` and then `free_pgtables()`, and
  the VMA stays reachable through rmap until inside the latter; an entry
  installed in that window is freed with the table.
- Rmap lock only, freeing: `retract_page_tables()` detaches and frees an
  empty PTE table under `i_mmap_lock_read()`, not the write lock, plus the
  PMD and PTE locks, through `pte_free_defer()`.
