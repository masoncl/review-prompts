- Unsharing frees no table and records no table in the `struct mmu_gather`;
  it records a range and the flags `unshared_tables` and
  `fully_unshared_tables`.
- The wait: `tlb_remove_table_sync_one()` in `tlb_flush_unshared_tables()`,
  called from `huge_pmd_unshare_flush()`, after the TLB flush.
- Condition for the IPI: `fully_unshared_tables`, set by
  `tlb_unshare_pmd_ptdesc()` only when its decrement left the table unshared.
- `tlb_flush_mmu_tlbonly()` before `huge_pmd_unshare_flush()`, as in
  `hugetlb_change_protection()`: `__tlb_reset_range()` clears
  `unshared_tables` but not `fully_unshared_tables`, so the IPI is still sent.
