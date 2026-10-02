- `force_flush` in the zap path: set in two places only, both in
  `zap_present_folio_ptes()` in `mm/memory.c`.
  - dirty entry of a non-anon folio, when `tlb_delay_rmap()` yields `true`;
  - `__tlb_remove_folio_pages()` returns `true` (batch full), which also sets
    `force_break`.
- `tlb_delay_rmap()`: sets `tlb->delayed_rmap`; `__tlb_remove_folio_pages()`
  only tags the page with `ENCODED_PAGE_BIT_DELAY_RMAP`, it does not report it.
- `tlb_delay_rmap()` without `CONFIG_SMP`, or with
  `CONFIG_MMU_GATHER_NO_GATHER` (s390 selects it): constant `false` in
  `include/asm-generic/tlb.h`; rmap is removed at once under the PTL and a
  dirty entry forces no flush.
- `tlb_flush_rmaps()`: walks only `tlb->local` and `tlb->active`;
  `tlb_next_batch()` refuses a new batch while `tlb->delayed_rmap` is set and
  `tlb->active` is not `tlb->local`, which is what forces the batch-full
  flush.
- `zap_empty_pte_table()`: clears the PMD entry while the PTE lock is still
  held, before the forced flush; skipped after `need_resched()` or
  `force_break`.
- Emptied PTE table: handed to `pte_free_tlb()` after `pte_unmap_unlock()`;
  it sets no `force_flush` and waits for the gather.
- `move_ptes()` flush placement: tied to the old and the new PTL; both are
  released only after `flush_tlb_range()` on the old range.
- `move_ptes()` rmap locks: `take_rmap_locks()` first, `drop_rmap_locks()` last,
  when `pmc->need_rmap_locks`; they bracket the whole function, error paths
  included, not the flush in particular.
- `pmc->need_rmap_locks`: a field of `struct pagetable_move_control` in
  `mm/internal.h`, not a parameter of `move_ptes()`.
- Lazy MMU mode: `zap_pte_range()` and `move_ptes()` both call
  `lazy_mmu_mode_disable()` before the flush.
