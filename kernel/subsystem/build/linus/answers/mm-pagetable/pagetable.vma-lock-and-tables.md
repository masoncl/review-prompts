- `collapse_huge_page()`: never frees the PTE table. At PMD order it
  deposits it with `pgtable_trans_huge_deposit()`; below PMD order it puts
  it back with `pmd_populate()`.
- `collapse_huge_page()` below PMD order: the PMD is none from
  `pmdp_collapse_flush()` until it is reinstalled; the mmap write lock,
  `vma_start_write()` and the anon_vma write lock are all held for that
  whole time.
- `collapse_huge_page()` at PMD order: drops the anon_vma lock once every
  page is isolated and locked.
- `zap_vma_range_batched()`: defined in `mm/memory.c`; asserts no lock, it
  checks `tlb->mm == vma->vm_mm`. zap_page_range_single_batched is not in
  this tree.
- madvise under a VMA read lock: `get_lock_mode()` in `mm/madvise.c`
  returns `MADVISE_VMA_READ_LOCK` for `MADV_DONTNEED`,
  `MADV_DONTNEED_LOCKED`, `MADV_FREE`, `MADV_GUARD_INSTALL` and
  `MADV_GUARD_REMOVE`.
- madvise fallback: `try_vma_read_lock()` takes the mmap read lock when
  `lock_vma_under_rcu()` fails or `is_vma_lock_sufficient()` is false: the
  range leaves the VMA, the mm is remote, the VMA has `userfaultfd_armed()`,
  or `MADV_GUARD_INSTALL` finds an anonymous VMA with no `anon_vma`.
- Other changers under a VMA read lock only: search for
  `lock_vma_under_rcu()`; besides faults, userfaultfd, TCP zerocopy and
  binder, `damon_va_walk_page_range()` in `mm/damon/vaddr.c` walks with
  `PGWALK_VMA_RDLOCK_VERIFY`.
- `MADV_DONTNEED` under a VMA read lock: sets `reclaim_pt`, so under
  `CONFIG_PT_RECLAIM` it can free a PTE table with no mmap lock held.
