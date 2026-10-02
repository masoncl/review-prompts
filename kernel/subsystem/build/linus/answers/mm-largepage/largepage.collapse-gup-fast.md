- `tlb_remove_table_sync_one()`: an IPI broadcast only with
  `CONFIG_MMU_GATHER_RCU_TABLE_FREE`; an empty inline in
  `include/asm-generic/tlb.h` otherwise, where the TLB flush in
  `pmdp_collapse_flush()` is the only wait.
- x86: `arch/x86/Kconfig` selects `MMU_GATHER_RCU_TABLE_FREE` unconditionally,
  so the call is a real IPI there.
- Refcount test after the sync: `folio_expected_ref_count()` compared with
  `folio_ref_count()` in `__collapse_huge_page_isolate()`; there is no
  is_refcount_suitable().
- File paths `retract_page_tables()` and `try_collapse_pte_mapped_thp()`: call
  `pmdp_get_lockless_sync()` after `pmdp_collapse_flush()`, not
  `tlb_remove_table_sync_one()`.
- `pmdp_get_lockless_sync()` in `include/linux/pgtable.h`: empty unless
  `CONFIG_GUP_GET_PXX_LOW_HIGH` is set and `CONFIG_PGTABLE_LEVELS` > 2.
- Clearing PTEs in place under the PTE lock, PMD still set: needs no IPI;
  `try_collapse_pte_mapped_thp()` does it, and `gup_fast_pte_range()` rereads
  the PTE after taking its reference.
- **Potentially unsafe usage**: detaching a PTE table with
  `pmdp_collapse_flush()` and not calling `tlb_remove_table_sync_one()` before
  going on.
  - Unsafe: when the table is kept, deposited or re-installed, as an anonymous
    collapse does. A walker that entered before the clear can be reading the
    table when it is refilled, and `zap_deposited_table()` in
    `mm/huge_memory.c` frees a deposited table with `pte_free()`, with no grace
    period.
  - Safe: when the table is already empty and goes to `pte_free_defer()`, as
    `retract_page_tables()` does. `gup_fast_pte_range()` maps the table with
    `pte_offset_map()`, which holds `rcu_read_lock()` until `pte_unmap()`, and
    `pte_free_defer()` in `mm/pgtable-generic.c` frees through `call_rcu()`.
