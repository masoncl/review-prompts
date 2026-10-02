- `zap_empty_pte_table()`: the no-rescan path, called with the PTL still
  held; `zap_pte_table_if_empty()`: the rescan path, called after the PTL
  was dropped. Both are in `mm/memory.c`.
- No rescan needs all of: `can_reclaim_pt`, `direct_reclaim`,
  `addr == end`, and the pmd lock obtained by `spin_trylock()` (or being the
  same lock as the PTL).
- `direct_reclaim`: cleared on a `need_resched()` or `force_break` exit and
  never set again, so a table zapped in more than one PTL hold always takes
  the rescan path.
- `any_skipped`: clears `can_reclaim_pt`, which disables both paths for that
  table.
- `zap_pte_table_if_empty()` lock order: `pmd_lock()`, then
  `pte_offset_map_rw_nolock()`, then the PTL with `SINGLE_DEPTH_NESTING`.
- `zap_pte_table_if_empty()`: does not call `pmd_same()`; the PMD is read
  with the pmd lock already held. It scans all `PTRS_PER_PTE` entries with
  `pte_none()` before `pmd_clear()`.
- After either path: `zap_pte_range()` calls `pte_free_tlb()` and
  `mm_dec_nr_ptes()` with no page table lock held.
- `retract_page_tables()`: an intended weaker recheck; it accepts a
  different table at the same PMD, because the folio lock held by
  `collapse_file()` blocks page faults on it, and repeats only
  `file_backed_vma_is_retractable()` under the PTL.
