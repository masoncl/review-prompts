- `folio_lruvec_lock_irq()`, `folio_lruvec_lock_irqsave()` and
  `folio_lruvec_lock()`, in `mm/memcontrol.c` under `CONFIG_MEMCG`: return
  with `lruvec->lru_lock` and the RCU read lock both held; so do the inline
  forms in `include/linux/memcontrol.h` without `CONFIG_MEMCG`.
- Unlock: `lruvec_unlock_irq()`, `lruvec_unlock_irqrestore()` or
  `lruvec_unlock()` in `include/linux/memcontrol.h`; each drops the spinlock
  and the RCU read lock.
- Lruvec binding: clearing `PG_lru` does not fix the folio's lruvec; the
  memcg, and so the result of `folio_lruvec()`, can change through
  `memcg_reparent_objcgs()` until `lru_lock` is held.
- Lock helpers under `CONFIG_MEMCG`: retry until `lruvec_memcg()` equals
  `folio_memcg()`, so only an lruvec returned by them, or matched with
  `folio_matches_lruvec()` under the lock, is the folio's.
- Folio on a list: its list and placement flags change under `lru_lock`;
  `folio_batch_move_lru()` and `folio_isolate_lru()` clear `PG_lru` before
  they take it.
- Folio off the list: its holder changes placement flags without `lru_lock`;
  for example `shrink_folio_list()` calls `folio_set_active()` on an isolated
  folio, and `__lru_cache_activate_folio()` on one in the local `lru_add`
  batch.
- `lruvec_add_folio()`: does not touch `PG_lru`; `folio_batch_move_lru()`
  calls `folio_set_lru()` after it, `move_folios_to_lru()` before it, both
  inside the lock.
- `folio_isolate_lru()`: returns `bool`; false with nothing changed when
  `PG_lru` was already clear; it returns no errno.
- `folio_isolate_lru()` with a folio on an MGLRU generation list:
  `lru_gen_del_folio()` clears the `LRU_GEN_MASK` bits and sets `PG_active`
  when `lru_gen_is_active()` is true for the old generation.
- `isolate_folio()` in `mm/vmscan.c`: MGLRU reclaim passes `reclaiming` true
  to `lru_gen_del_folio()`, which then does not set `PG_active`.
- `folio_update_gen()`: rewrites the generation bits with `try_cmpxchg()`
  under the page table lock only, without `lru_lock`; `sort_folio()` moves
  the folio to the matching list later.
- `folio_isolate_lru()` caller: holds a reference, does not hold `lru_lock`,
  has IRQs enabled (`lruvec_unlock_irq()` enables them); a prior
  `folio_test_lru()` is not required.
- `VM_BUG_ON_FOLIO()` on a zero refcount in `folio_isolate_lru()`: a `BUG()`,
  and compiled out without `CONFIG_DEBUG_VM`.
- `folio_isolate_lru()` and `folio_putback_lru()`: declared in
  `mm/internal.h`; every caller is in `mm/`.
- **Potentially unsafe usage**: clearing `PG_lru` on a folio with no
  reference held.
  - Unsafe: when another task can drop the last reference at the same time;
    `__page_cache_release()` tests `folio_test_lru()` at refcount zero to
    decide whether to unlink the folio.
  - Safe: `folio_try_get()` first, then `folio_test_clear_lru()`, with
    `folio_put()` on failure, as `isolate_lru_folios()` does under
    `lru_lock`.
  - Safe: the caller already holds a reference, which `folio_isolate_lru()`
    asserts with `VM_BUG_ON_FOLIO()`.
  - Safe: `__folio_clear_lru_flags()` under `lru_lock` by the path that saw
    `folio_put_testzero()` return true, as `move_folios_to_lru()` does;
    `folio_try_get()` fails on such a folio.
