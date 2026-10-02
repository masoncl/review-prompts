- `pmd_trans_huge_lock()`: tests `pmd_is_huge()` locklessly, and
  `__pmd_trans_huge_lock()` tests it again under `pmd_lock()`.
- There is no pmd_devmap() here.
- Lock is returned held for any non-none non-present PMD, not only for a
  migration or device-private entry; the `pmd_is_valid_softleaf()` test is
  left to the caller.
- `__pmd_trans_huge_lock()` called directly: no lockless test, the lock is
  always taken; `zap_huge_pmd()`, `move_huge_pmd()` and `change_huge_pmd()` do
  this.
- `huge_pmd_set_accessed()`: takes no lock; `__handle_mm_fault()` holds
  `pmd_lock()` around it, and it only makes the `pmd_same()` test.
