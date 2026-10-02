- `lru_add_drain()`, `lru_cache_disable()`, `lru_cache_enable()`: in
  `mm/internal.h`; of the drain calls, `include/linux/swap.h` has only
  `lru_add_drain_all()` and `lru_cache_drain_for_folio()`.
- mlock batch: `lru_add_drain()` drains it with `mlock_drain_local()`, the
  per-CPU work of `lru_add_drain_all()` does too, and `mm/mlock.c` tests
  `lru_cache_disabled()` before it leaves a folio queued.
- `lru_cache_disable()`: waits with `synchronize_rcu_expedited()`, then, under
  `CONFIG_SMP`, calls `__lru_add_drain_all(true)`.
- `__lru_add_drain_all(true)`: the flag only skips the generation early exit;
  work is still queued only on CPUs where `cpu_needs_drain()` is true.
- `lru_cache_drain_for_folio()` in `mm/folio.c`: drains for one folio, and
  only when `folio_ref_count()` differs from `folio_expected_ref_count()`
  plus the caller's own references.
- `lru_cache_drain_for_folio()` order: `lru_add_drain()`, recheck, then
  `lru_add_drain_all()`; with a non-NULL `drained`, each level runs at most
  once over a series of folios.
- `lru_cache_drain_for_folio()` on a large folio: returns at once, since
  `folio_may_be_lru_cached()` is false.
- `collect_longterm_unpinnable_folios()` in `mm/gup.c`: calls
  `lru_cache_drain_for_folio()` per folio; it does not call
  `lru_add_drain_all()` directly and does not call `lru_cache_disable()`.
- CMA user of the `lru_cache_disable()` and `lru_cache_enable()` bracket:
  `__alloc_contig_migrate_range()` in `mm/page_alloc.c`.
- Between `lru_cache_disable()` and `lru_cache_enable()`: batches stay empty,
  but `folio_isolate_lru()` can still return false, because another isolator
  or a drain in progress has cleared `PG_lru`.
- **Potentially unsafe usage**: draining once, then isolating folios.
  - Unsafe: when the code has no path for `folio_isolate_lru()` returning
    false, or relies on batches staying empty after `lru_add_drain()` or
    `lru_add_drain_all()` returns; `__folio_batch_add_and_move()` queues
    again on any CPU unless `lru_cache_disabled()` is true.
  - Safe: between `lru_cache_disable()` and `lru_cache_enable()`, with the
    failure reported, as `do_pages_move()` in `mm/migrate.c`:
    `__add_folio_for_migration()` returns `-EBUSY`.
  - Safe: a drain as an optimisation, with the failure handled per folio,
    as `migrate_device_unmap()` in `mm/migrate_device.c`, which clears
    `MIGRATE_PFN_MIGRATE` for that entry.
  - Safe: `lru_cache_drain_for_folio()` then `folio_isolate_lru()`, skipping
    the folio on false, as `collect_longterm_unpinnable_folios()`.
