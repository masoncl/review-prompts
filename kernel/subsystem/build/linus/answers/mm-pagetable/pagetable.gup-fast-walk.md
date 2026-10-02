- Recheck after `try_grab_folio_fast()`: compares against
  `pmdp_get_lockless(pmdp)` and `ptep_get_lockless(ptep)`, not plain reads;
  under `CONFIG_GUP_GET_PXX_LOW_HIGH` these read the entry in two halves (the
  PMD only with more than two levels).
- `page_folio(page) != folio` test: in `try_get_folio()`, which drops the
  reference and retries; `gup_fast_pte_range()` has no such test of its own.
- IRQs off rather than `rcu_read_lock()`: `tlb_remove_table_sync_one()` is
  `smp_call_function()` with wait, not an RCU grace period, so only a walker
  with IRQs disabled holds it off.
- khugepaged: only `collapse_huge_page()` calls `tlb_remove_table_sync_one()`
  by name after `pmdp_collapse_flush()`; `try_collapse_pte_mapped_thp()` and
  `retract_page_tables()` call `pmdp_get_lockless_sync()` and then
  `pte_free_defer()`.
- `pmdp_get_lockless_sync()`: `tlb_remove_table_sync_one()` only under
  `CONFIG_GUP_GET_PXX_LOW_HIGH` with more than two levels; empty otherwise
  (`include/linux/pgtable.h`).
- A table detached for reuse has the same requirement as one that is freed:
  `tlb_flush_unshared_tables()` calls `tlb_remove_table_sync_one()` when
  `tlb->fully_unshared_tables` is set, before a hugetlb PMD table can be
  reused.
