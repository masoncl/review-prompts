- LRU code location: there is no mm/swap.c; `lru_add()`,
  `folio_batch_move_lru()` and `folio_mark_accessed()` are in `mm/folio.c`.

| Flag | Set | Cleared | Rule in this tree |
|---|---|---|---|
| writeback | `folio_test_set_writeback()` in `__folio_start_writeback()` | xor in `__folio_end_writeback()` | set asserts folio locked; xarray tags only if `mapping_use_writeback_tags()` |
| lru | `folio_set_lru()` in `folio_batch_move_lru()`, after the move function | `folio_test_clear_lru()`; `__folio_clear_lru_flags()` | `folio_test_clear_lru()` is atomic and needs no lruvec lock; the set in `folio_batch_move_lru()` and the final clear at refcount 0 are under it |
| active | `lru_activate()`; `__lru_cache_activate_folio()` | LRU move functions | lruvec lock on the LRU; in the local `lru_add` batch only the per-CPU local lock |
| swapbacked | `__folio_set_swapbacked()` on new folios; `ttu_anon_lazyfree_folio()`, `__discard_anon_folio_pmd_locked()` | `lru_lazyfree()` | clear runs at batch drain under the lruvec lock, not the folio lock |
| swapcache | `__swap_cache_do_add_folio()` | `__swap_cache_do_del_folio()` | folio lock plus the `struct swap_cluster_info` lock; there is no swap xarray |
| mlocked | `mlock_folio()`, `mlock_new_folio()` | `__munlock_folio()`; `__free_pages_prepare()` | atomic ops, except the non-atomic clear in `__free_pages_prepare()`; `__munlock_folio()` takes the lruvec lock only if `folio_test_clear_lru()` succeeded |
| unevictable | `lru_add()`, `__mlock_folio()`, `__mlock_new_folio()` | `lru_add()`, `__munlock_folio()`, `__mlock_folio()` | in these functions, under the lruvec lock |
| private | `folio_attach_private()` | `folio_detach_private()` | helpers take and drop a folio reference and make no lock assertion |

- `folio_xor_flags_has_waiters()`: `folio_unlock()`, `folio_end_read()` and
  `__folio_end_writeback()` flip their bits with it, so the bit must be known
  set (clear for uptodate in `folio_end_read()`) and no other path may change
  it at the same time; only `VM_BUG_ON_FOLIO()` checks this.
- `munlock_folio()`: does not clear the flag; it queues the folio, and
  `__munlock_folio()` clears it when the batch drains.
- `folio_test_swapcache()`: true only if swapbacked is also set, because
  `PG_swapcache` aliases `PG_owner_priv_1`.
- `PAGEFLAG(Private, private, PF_ANY)`: `SetPagePrivate()` on a tail page sets
  the tail's own bit.
- With `lru_gen_enabled()`: `lru_gen_add_folio()` clears `PG_active` when the
  folio goes on a generation list and `lru_gen_del_folio()` sets it again for
  an active generation when not reclaiming, both by `set_mask_bits()` on the
  whole word.
- With `lru_gen_enabled()`: `folio_mark_accessed()` only calls
  `lru_gen_inc_refs()`, which updates `PG_referenced`, the refs field and
  `PG_workingset`.
- `__folio_clear_active()` and `__folio_clear_unevictable()`: used only at
  refcount 0, in `__folio_clear_lru_flags()` and in the dead-folio branch of
  `folio_batch_move_lru()` after `folio_ref_freeze(folio, 1)`.
- An isolated folio that still has references: use the atomic forms, as
  `lru_move_tail()` and `folio_migrate_flags()` do.
