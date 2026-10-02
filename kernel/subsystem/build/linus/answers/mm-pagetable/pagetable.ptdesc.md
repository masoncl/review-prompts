- Destructor: there is no pagetable_pte_dtor() or pagetable_pmd_dtor() here;
  `pagetable_dtor()` in `include/linux/mm.h` serves every level, and
  `pagetable_dtor_free()` is that plus `pagetable_free()`.
- `init_mm`: `pagetable_pte_ctor()` and `pagetable_pmd_ctor()` skip the lock
  init when `mm == &init_mm`, so for a table constructed for `init_mm` they
  cannot fail.
- Skipped `pagetable_dtor()`: no bad-page report; `free_pages_prepare()` in
  `mm/page_alloc.c` resets a leftover page type silently.
- Skipped `pagetable_dtor()`, what stays wrong: `NR_PAGETABLE` is never
  subtracted, and under `CONFIG_SPLIT_PTE_PTLOCKS` with `ALLOC_SPLIT_PTLOCKS`
  the lock from `ptlock_alloc()` leaks.
- Deferred frees: the dtor runs inside the callback, not before it is queued,
  in `pte_free_now()` in `mm/pgtable-generic.c` and, under
  `CONFIG_MMU_GATHER_TABLE_FREE`, in `__tlb_remove_table()` in
  `include/asm-generic/tlb.h`.
- Without `CONFIG_MMU_GATHER_TABLE_FREE`: `tlb_remove_table()` calls
  `pagetable_dtor()` before it queues the page with `tlb_remove_page()`.
- `pagetable_free()` versus `__free_pages()`: `pagetable_free()` hands a table
  marked with `ptdesc_set_kernel()` to `pagetable_free_kernel()`; a direct
  `__free_pages()` skips that.
- `pagetable_free_kernel()` under `CONFIG_ASYNC_KERNEL_PGTABLE_FREE`: frees
  from a workqueue, after `iommu_sva_invalidate_kva_range()`; see
  `mm/pgtable-generic.c`.
