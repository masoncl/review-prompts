- Table pages, `CONFIG_MMU_GATHER_RCU_TABLE_FREE`: a batch is freed by
  `call_rcu()` after the flush. The gather never frees a table after an IPI
  sync.
- `CONFIG_MMU_GATHER_TABLE_FREE`: selected only by
  `MMU_GATHER_RCU_TABLE_FREE` (`arch/Kconfig`), so the non-RCU
  `tlb_remove_table_free()` in `mm/mmu_gather.c`, which frees directly with
  no wait, is built in no configuration.
- `tlb_table_invalidate()`: flushes before tables are freed only if
  `tlb_needs_table_invalidate()` is true.
- `tlb_remove_table()` with a full batch (`MAX_TABLE_BATCH`): flushes and
  hands the tables to `call_rcu()` at once, while pages stay batched until
  the next `tlb_flush_mmu()`.
- `tlb_finish_mmu()`: starts with
  `VM_WARN_ON_ONCE(tlb->fully_unshared_tables)`; a gather that unshared a
  hugetlb PMD table must have gone through `huge_pmd_unshare_flush()` first.
- `mm_tlb_flush_nested()` in `tlb_finish_mmu()`: also true while
  `wp_clean_pre_vma()` in `mm/mapping_dirty_helpers.c` has raised
  `mm->tlb_flush_pending`; that path uses no gather.
