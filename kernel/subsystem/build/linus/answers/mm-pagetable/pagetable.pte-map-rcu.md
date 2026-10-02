- RCU guarantee, precondition: it holds only while the caller keeps the VMA
  attached and the mm in use; see the last paragraph of the comment above
  `pte_offset_map_lock()`.
- `free_pgtables()`: takes no page table lock and frees through
  `pte_free_tlb()`, which is deferred by RCU only under
  `CONFIG_MMU_GATHER_RCU_TABLE_FREE`.
- Immediate free, for example: `arch/arc/include/asm/pgalloc.h` defines
  `__pte_free_tlb()` as `pte_free()`.
- Paths that do wait for a grace period: `pte_free_defer()` and the
  `CONFIG_PT_RECLAIM` free in `zap_pte_range()`; that option depends on
  `MMU_GATHER_RCU_TABLE_FREE`.
