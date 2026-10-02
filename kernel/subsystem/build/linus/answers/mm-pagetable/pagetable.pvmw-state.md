- `pvmw->pte` set on a non-hugetlb VMA: the caller is also inside the
  `rcu_read_lock()` taken by `__pte_offset_map()`; hugetlb `pvmw->pte` comes
  from `hugetlb_walk()` with no map and no RCU section.
- Lock coverage across calls: the next call keeps `pvmw->ptl` while it stays in
  the same PTE table; at a table boundary it unlocks, unmaps and sets
  `PVMW_PGTABLE_CROSSED` in `pvmw->flags`, so entries returned earlier are no
  longer locked.
- `PVMW_PGTABLE_CROSSED`: never cleared by the walker; `folio_referenced_one()`
  and `try_to_unmap_one()` test it before `mlock_vma_folio()`.
- `page_vma_mapped_walk_done()`: clears no field; `not_found()` has already
  called it on every false return that held `pvmw->ptl`, so a second call
  unlocks `pvmw->ptl` again.
- `page_vma_mapped_walk_restart()`: needs `pvmw->ptl` held and `pvmw->pmd` or
  `pvmw->pte` set, and warns otherwise.
- `page_vma_mapped_walk_restart()`: unlocks and sets `ptl`, `pmd`, `pte` to
  NULL; it does not call `pte_unmap()` and does not touch `pvmw->address`.
- **Unsafe usage**: `page_vma_mapped_walk_restart()` while `pvmw->pte` is
  mapped on a non-hugetlb VMA.
  - Unsafe: the pointer is set to NULL with no `pte_unmap()`, so the
    `rcu_read_lock()` of `__pte_offset_map()` is never dropped.
  - Safe: after a PMD-level return (`pvmw->pte` NULL), as `try_to_unmap_one()`
    does after `split_huge_pmd_locked()`.
- **Potentially unsafe usage**: changing `pvmw->pte` or `pvmw->address`
  between calls.
  - Unsafe: when the two no longer match, or the new position leaves the PTE
    table that `pvmw->ptl` locks; the next call resumes from these fields.
  - Safe: advancing both by the same count inside one table, as
    `folio_referenced_one()` does with a batch bounded by `pmd_addr_end()`;
    `page_vma_mapped_walk()` then steps both by one and tests the table
    boundary on `pvmw->address`.
