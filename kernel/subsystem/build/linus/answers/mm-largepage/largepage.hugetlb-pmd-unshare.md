- `tlb_unshare_pmd_ptdesc()` in `include/asm-generic/tlb.h`: does the count
  decrement, adds the `PUD_SIZE` range to the gather and sets
  `unshared_tables`; `huge_pmd_unshare()` itself only clears the PUD and
  calls `mm_dec_nr_pmds()`.
- Left to the caller: `huge_pmd_unshare_flush()` before `i_mmap_rwsem` is
  dropped.
- `huge_pmd_unshare_flush()`: asserts only `i_mmap_assert_write_locked()`.
- Hugetlb VMA lock and page table lock: not needed for the flush.
- `__huge_pmd_unshare()` assertions: run only when the size is `PMD_SIZE` and
  the table is shared, so lockdep is silent about a missing lock otherwise.
- `hugetlb_vma_assert_locked()`: `lockdep_assert_held()`, so read mode passes.
- `hugetlb_split()`: unshares with `check_locks` false, without the hugetlb
  VMA lock.
- Page table lock: required by the kerneldoc of `huge_pmd_unshare()`;
  nothing asserts it.
- `try_to_unmap_one()` does not call `huge_pmd_unshare()`; in `mm/rmap.c`
  `try_to_unmap_poisoned_hugetlb_one()` and `try_to_migrate_one()` do.
- **Unsafe usage**: calling `huge_pmd_unshare_flush()` after
  `i_mmap_rwsem` was dropped, or leaving the flush to `tlb_finish_mmu()`,
  which has `VM_WARN_ON_ONCE()` on `fully_unshared_tables`.
  - Safe: dropping the hugetlb VMA lock before the flush while
    `i_mmap_rwsem` stays held for write, as `try_to_migrate_one()` does;
    `huge_pmd_unshare_flush()` asserts only `i_mmap_rwsem`.
  - Safe: dropping the page table lock before the flush, as
    `__unmap_hugepage_range()` does; `huge_pmd_unshare_flush()` does not
    assert it.
