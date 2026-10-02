- Per-CPU batch, large folio: holds its reference only inside the queueing
  call. `__folio_batch_add_and_move()` in `mm/folio.c` and `mlock_folio()`,
  `mlock_new_folio()`, `munlock_folio()` in `mm/mlock.c` drain the batch at
  once when `folio_may_be_lru_cached()` is false, which it is for every large
  folio.
- Per-CPU batch while `lru_cache_disabled()`: drained in the same call too,
  for small folios as well.
- Batches: the members of `struct cpu_fbatches`, including
  `lru_deactivate_file` and `lru_move_tail`, plus `mlock_fbatch` in
  `mm/mlock.c`.
- `PG_lru` set does not rule out a batch reference: every batch of
  `struct cpu_fbatches` except `lru_add` is fed only with folios that are on
  the LRU, for example by `folio_activate()` (with `CONFIG_SMP`) and
  `folio_rotate_reclaimable()`.
- `lru_add` drain: `folio_batch_move_lru()` frees a folio whose only
  reference is the batch's (`folio_ref_freeze(folio, 1)`) instead of putting
  it on the LRU, and stores NULL in its slot; `folios_put_refs()` skips NULL
  slots.
- Pins: see "Recording a pin".
