Rows not listed here are where models expect them.

| Job | File in this tree |
|---|---|
| Map and lock a PTE table | `pte_offset_map_lock()` is declared in `include/linux/mm.h` and defined in `mm/pgtable-generic.c`; `pte_offset_map()` is an inline in `include/linux/mm.h`, not in `include/linux/pgtable.h` |
| Typed helpers for non-present entries | `include/linux/leafops.h` (`softleaf_from_pte()`, `softleaf_is_migration()`, `enum softleaf_type`); `softleaf_t` is a typedef of `swp_entry_t` in `include/linux/mm_types.h`. pte_to_swp_entry, is_swap_pte, is_migration_entry, is_pte_marker and non_swap_entry are defined nowhere |
| Swap entry encoding | `include/linux/swapops.h` holds `swp_entry()` and the constructors, for example `make_readable_migration_entry()`; there is no make_migration_entry. Type numbers (`SWP_MIGRATION_READ`, `SWP_PTE_MARKER`) are in `include/linux/swap.h` |
| Reverse-map walker | `mm/rmap.c` picks the VMAs; `mm/page_vma_mapped.c` walks inside one VMA; KSM folios go to `rmap_walk_ksm()` in `mm/ksm.c` |
| Reclaim of empty PTE tables | there is no mm/pt_reclaim.c and no try_to_free_pte. The code is static in `mm/memory.c`: `zap_pte_range()` calls `pte_table_reclaim_possible()`, `zap_empty_pte_table()` and `zap_pte_table_if_empty()`. In `mm/mmu_gather.c`, `CONFIG_PT_RECLAIM` selects the `call_rcu()` form of `__tlb_remove_table_one()`; the option is in `mm/Kconfig` |
