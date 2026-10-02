- `flush_tlb_batched_pending()` in `mm/rmap.c`: calls `flush_tlb_mm()`
  directly; there is no arch_flush_tlb_batched_pending() here.
- `mm->tlb_flush_batched`: the field `flush_tlb_batched_pending()` tests; it
  packs a pending and a flushed count, see `TLB_FLUSH_BATCH_FLUSHED_SHIFT`.
- `mm->tlb_flush_pending`: a separate counter, raised by `tlb_gather_mmu()`
  through `inc_tlb_flush_pending()`; `flush_tlb_batched_pending()` does not
  read it.
- Without `CONFIG_ARCH_WANT_BATCHED_UNMAP_TLB_FLUSH`:
  `flush_tlb_batched_pending()` is an empty stub in `mm/internal.h` and
  `mm->tlb_flush_batched` does not exist.
- Producers: `set_tlb_ubc_flush_pending()` is called from `try_to_unmap_one()`
  and from `try_to_migrate_one()`; the entry left behind may be a migration
  entry.
- `TTU_BATCH_FLUSH` outside reclaim: passed for example by `unmap_folio()` in
  `mm/huge_memory.c`.
- `set_tlb_ubc_flush_pending()`: returns without recording anything when
  `!pte_accessible()`.
- `should_defer_flush()`: also needs `arch_tlbbatch_should_defer()`; on x86
  that is `true` only if another CPU is in `mm_cpumask()`.
- Level: both `set_tlb_ubc_flush_pending()` calls are on the `pvmw.pte` branch;
  all seven `flush_tlb_batched_pending()` call sites are PTE loops, none is in
  `mm/huge_memory.c`.
- Position: every call site sits between taking the PTL and
  `lazy_mmu_mode_enable()`.
- Relock in `madvise_free_pte_range()` and
  `madvise_cold_or_pageout_pte_range()`:
  - `start_pte` takes the result of the relock, so a failed relock can `break`
    and the exit path, which tests `start_pte`, skips `pte_unmap_unlock()`;
  - `nr = 0` after a successful `split_folio()`, so the same slot is read
    again with `ptep_get()`.
- **Unsafe usage**: calling `flush_tlb_batched_pending()` before the PTL is
  held, or once ahead of a loop that drops and retakes the PTL.
  - Safe: one call per lock acquisition, as `zap_pte_range()` does by jumping
    back to its `retry` label.
  - Safe: one call in a function that never drops the PTL, as
    `change_pte_range()` does.
  - Safe: with two tables, one call after both PTLs are held, as `move_ptes()`
    does after `spin_lock_nested()` on the new PTL.
