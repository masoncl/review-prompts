- Move batches (`lru_deactivate_file`, `lru_deactivate`, `lru_lazyfree`,
  `lru_activate`, `lru_move_tail`): queueing does not clear `PG_lru` or take
  the folio off its list.
- Queue-time test, for example in `folio_deactivate()`: a plain
  `folio_test_lru()`; a folio that fails it is not queued.
- Move batches at drain: `folio_batch_move_lru()` calls
  `folio_test_clear_lru()`; a folio isolated while queued is skipped there and
  only loses the batch reference.
- `lru_activate`: the member name of the activate batch; it exists only under
  `CONFIG_SMP`.
- Batch capacity: `FOLIO_BATCH_SIZE` in `include/linux/folio_batch.h`; there
  is no PAGEVEC_SIZE.
- New folio in a `VM_LOCKED` VMA with no `VM_SPECIAL` bit:
  `folio_add_lru_vma()` queues it on `mlock_fbatch` in `mm/mlock.c`, not on
  `lru_add`; that batch also holds a reference, and is drained on the same
  conditions as in `__folio_batch_add_and_move()`: batch full,
  `folio_may_be_lru_cached()` false, or `lru_cache_disabled()` true.
