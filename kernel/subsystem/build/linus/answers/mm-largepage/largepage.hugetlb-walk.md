- `huge_pte_lockptr()` in `include/linux/hugetlb.h` chooses by huge page size:

| Size | Lock |
|---|---|
| >= `PUD_SIZE` | `pud_lockptr()` |
| >= `PMD_SIZE`, or `CONFIG_HIGHPTE` | `pmd_lockptr()` |
| smaller | `ptep_lockptr()` |

- Hugetlb VMA lock: `hugetlb_fault()` holds it in addition to `mmap_lock` or
  the per-VMA lock, not instead of them; rmap walkers such as
  `try_to_migrate_one()` hold it with `i_mmap_rwsem` and without `mmap_lock`.
- `hugetlb_split()`: unshares without the hugetlb VMA lock; it asserts
  `vma_assert_write_locked()` and `i_mmap_assert_write_locked()` instead.
- `i_mmap_rwsem`: `__huge_pmd_unshare()` reaches `pud_clear()` only after
  `i_mmap_assert_write_locked()`; the comment above `huge_pte_offset()` in
  `include/linux/hugetlb.h` says a holder is not protected from unsharing.
- Private mapping: `hugetlb_wp()` calls `hugetlb_walk()` under the per-VMA
  lock too; `hugetlb_fault()` calls `vma_end_read()` on `VM_FAULT_RETRY`.
- **Potentially unsafe usage**: using a `pte_t *` from `hugetlb_walk()` after
  the hugetlb VMA lock was dropped.
  - Unsafe: on a VMA that passes `__vma_shareable_lock()`, when
    `i_mmap_rwsem` is not held either; the PUD can be cleared and the pointer
    is into a table this mm no longer maps.
  - Safe: while `i_mmap_rwsem` is still held, which `__huge_pmd_unshare()`
    asserts write-held, as `try_to_migrate_one()` does after
    `hugetlb_vma_unlock_write()`.
  - Safe: on a VMA without `VM_MAYSHARE`, which `want_pmd_share()` never
    shares; `hugetlb_wp()` drops the lock around `unmap_ref_private()` there,
    then walks again and compares with `pte_same()`.
