- There is no lruvec_memcg_debug() and no unlock_page_lruvec() in this tree.
- `folio_lruvec_lock()`, `folio_lruvec_lock_irq()`,
  `folio_lruvec_lock_irqsave()` in `mm/memcontrol.c`: compare only
  `lruvec_memcg()` with `folio_memcg()`; on mismatch they drop the spinlock,
  keep RCU, and retry.
- `folio_matches_lruvec()`: also compares the pgdat; used by the relock
  helpers and the `VM_WARN_ON_ONCE_FOLIO()` checks in
  `include/linux/mm_inline.h`.
- Recheck relies on an LRU folio holding the objcg of its own node; see
  `charge_memcg()` and `get_migration_objcg()` in `mm/memcontrol.c`, both
  select by `folio_nid()`.
- Precondition: folio→objcg already stable (folio locked, LRU flag clear, or
  refcount frozen); batch callers do `folio_test_clear_lru()` first, hold a
  folio that is not on the LRU, or act on a folio whose refcount reached
  zero.
- Held on return: `lru_lock` and the RCU read lock, also in the
  `!CONFIG_MEMCG` stubs.
- Release: `lruvec_unlock()`, `lruvec_unlock_irq()`,
  `lruvec_unlock_irqrestore()` in `include/linux/memcontrol.h`; each drops
  the spinlock, then RCU.
- `lruvec_lock_irq()` (lock by lruvec, no folio): takes RCU too, so it pairs
  with `lruvec_unlock_irq()`.
- Batch users of the relock helpers are in `mm/folio.c`, `mm/mlock.c` and
  `mm/vmscan.c`; there is no mm/swap.c in this tree.
- Second batching form: `isolate_migratepages_block()` in
  `mm/compaction.c` compares `folio_lruvec()` with the lruvec it holds and
  relocks through `compact_folio_lruvec_lock_irqsave()`, its own copy of the
  retry loop.
- **Unsafe usage**: taking `lru_lock` on a `folio_lruvec()` result with no
  recheck after the lock is held.
  - Unsafe: also with the folio locked or isolated; `objcg->memcg` can move
    to the parent between lookup and lock, and the lock taken is then the
    dying child's.
  - Safe: `folio_lruvec_lock_irq()` and its variants, as
    `folio_isolate_lru()` does.
  - Safe: a folio compared with a lruvec already locked, by
    `folio_matches_lruvec()` as `folio_lruvec_relock_irq()` does, or by
    `folio_lruvec()` as `isolate_migratepages_block()` does;
    `__memcg_reparent_objcgs()` runs only with both `lru_lock`s held, so a
    match cannot change.
