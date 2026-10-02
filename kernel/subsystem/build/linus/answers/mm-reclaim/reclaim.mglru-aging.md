- `walk_pte_range()`: takes the PTE lock with `spin_trylock()`.
- `walk_pmd_range_locked()`: takes the PMD lock with `spin_trylock()`; it is
  the only place the walk takes a lock from `pmd_lockptr()`.
- There is no should_skip_mm() here; `get_next_mm()` skips an mm only when
  its node bit in `mm->lru_gen.bitmap` is clear and `walk->force_scan` is
  false, and pins the mm with `mmgrab()`.
- `try_to_inc_max_seq()` with `seq <= mm_state->seq`: returns false and does
  not call `inc_max_seq()`.
- Without `CONFIG_LRU_GEN_WALKS_MMU`: `get_mm_state()` returns NULL and
  `try_to_inc_max_seq()` calls `inc_max_seq()` directly.
- `iterate_mm_list_nowalk()`: used when `should_walk_mmu()` is false or
  `set_mm_walk()` returns NULL.
- Walk pause: `walk_pud_range()` tests `need_resched()` and
  `walk->batched >= MAX_LRU_BATCH`; the walk has no signal test.
- `try_to_inc_max_seq_nowalk()`: a second way to advance `max_seq` with no
  walk, used by `max_lru_gen_memcg()` before reparenting; it advances
  `mm_state->seq` and leaves `mm_state->head` and `mm_state->tail` alone.
- `reset_batch_size()`: locks with `lruvec_live_lock_irq()`, which returns an
  ancestor's lruvec when the memcg is dying; the sizes are applied there.
- `lru_gen_look_around()` without a walk: `folio_activate()` can take the lru
  lock while the PTE lock is held.
- `folio_activate()` path: takes the folio off its list and re-adds it with
  `PG_active`; `lru_gen_folio_seq()` then gives `max_seq` if `PG_workingset`
  is set, else `max_seq - 1`.
