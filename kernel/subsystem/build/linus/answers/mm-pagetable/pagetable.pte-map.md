- NULL cases: decided only in `__pte_offset_map()`: PMD none, not present,
  `pmd_trans_huge()`, or `pmd_bad()`; there is no devmap test in this tree.
- `pmd_same()` mismatch in `pte_offset_map_lock()`: not a NULL return; it
  unlocks, unmaps and retries, and returns NULL only if the re-read PMD
  fails the tests above.
- `pte_offset_map_ro_nolock()` and `pte_offset_map_rw_nolock()`: make no
  `pmd_same()` test at all.
- On NULL: the RCU read lock is already dropped and `*ptlp` is not written,
  so the caller must not call `pte_unmap()` or touch `ptl`.
- `*pmdvalp` on NULL: it is written, with the value that failed the test.
- **Potentially unsafe usage**: writing entries after
  `pte_offset_map_rw_nolock()` and `spin_lock(ptl)` with no
  `pmd_same()` recheck.
  - Unsafe: when the entry the caller expects is none, or it compares no
    entry; a detached table is empty, so the check passes on it. The mmap
    write lock alone does not help: `retract_page_tables()` detaches under
    `i_mmap_rwsem` held for read.
  - Safe: `pmd_same(pmdval, pmdp_get_lockless(pmd))` under the lock, as
    `map_pte()` in `mm/page_vma_mapped.c` does.
  - Safe: `pte_same()` against an entry read earlier that is not none, as
    `handle_pte_fault()` does; `move_pages_ptes()` in `mm/userfaultfd.c`
    adds `pmd_same()` for its none destination for this reason.
  - Safe: `pmd_lock()` held from before the map until after the write, as
    `zap_pte_table_if_empty()` in `mm/memory.c` does.
