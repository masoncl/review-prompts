- `tlb_remove_table()` batch allocation failure, `CONFIG_PT_RECLAIM`:
  `tlb_table_invalidate()`, then `call_rcu()` on `pt_rcu_head` of the
  `struct ptdesc`; does not sleep.
- `tlb_remove_table()` batch allocation failure, no `CONFIG_PT_RECLAIM`:
  `tlb_table_invalidate()`, then `tlb_remove_table_sync_rcu()`, then the
  table is freed at once. It does not call `tlb_remove_table_sync_one()`.
- `tlb_remove_table_sync_rcu()`: is `synchronize_rcu()`, so the
  allocation-failure path of `tlb_remove_table()` without
  `CONFIG_PT_RECLAIM` can sleep.
- `CONFIG_PT_RECLAIM`: not selectable; `def_bool y`, depends on
  `MMU_GATHER_RCU_TABLE_FREE && !HAVE_ARCH_TLB_REMOVE_TABLE` (`mm/Kconfig`).
- Without `CONFIG_MMU_GATHER_RCU_TABLE_FREE`:
  `tlb_remove_table_sync_one()` and `tlb_remove_table_sync_rcu()` are empty
  stubs in `include/asm-generic/tlb.h`, and `tlb_remove_table()` puts the
  table in the page batch, freed after the flush with no wait.

| Function | Waits for | Frees |
|---|---|---|
| `tlb_remove_table()` (through `pte_free_tlb()` and the like) | under `CONFIG_MMU_GATHER_RCU_TABLE_FREE`, an RCU grace period: `call_rcu()` for a batch | yes, later |
| `pte_free_defer()` | an RCU grace period, by `call_rcu()` | yes, later |
| `tlb_remove_table_sync_one()` | every other CPU to take an IPI, so to leave any IRQs-off walk | no |
| `tlb_remove_table_sync_rcu()` | an RCU grace period, blocking | no |

- `tlb_remove_table_sync_one()` called by name: only in
  `collapse_huge_page()` and `tlb_flush_unshared_tables()`, both for a table
  that is kept, not freed. `pmdp_get_lockless_sync()` is a macro for it
  under `CONFIG_GUP_GET_PXX_LOW_HIGH` with `CONFIG_PGTABLE_LEVELS` above 2,
  and that one runs before `pte_free_defer()`.
- Generic `pte_free_defer()` in `mm/pgtable-generic.c`: compiled only with
  `CONFIG_TRANSPARENT_HUGEPAGE`; powerpc, s390 and sparc define their own.
