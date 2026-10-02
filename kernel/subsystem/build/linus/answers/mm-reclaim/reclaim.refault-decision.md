- There is no lru_note_cost_refault() in this tree; `workingset_refault()`
  does not charge refault cost.
- Classic LRU, not recent: only `WORKINGSET_REFAULT_BASE + file` is counted;
  the workingset bit of the shadow is ignored.
- Classic LRU, recent: `folio_set_active()`, `workingset_age_nonresident()`
  on the refaulting folio's lruvec, `WORKINGSET_ACTIVATE_BASE + file`.
- `folio_set_workingset()` and `WORKINGSET_RESTORE_BASE + file`: only when
  recent and the shadow's workingset bit is set.
- Workingset size in `workingset_test_recent()`, file folio:
  `NR_ACTIVE_FILE`, plus `NR_ACTIVE_ANON` and `NR_INACTIVE_ANON` when
  `mem_cgroup_get_nr_swap_pages()` is above 0.
- Workingset size, anon folio: `NR_ACTIVE_FILE` and `NR_INACTIVE_FILE`, plus
  `NR_ACTIVE_ANON` when swap is available.
- Unpacked counter: shifted left by `bucket_order[file]`; the distance is
  masked with `EVICTION_MASK` or `EVICTION_MASK_ANON` by type.
- `lru_gen_refault()`: counts nothing and changes nothing when the shadow's
  lruvec is not `folio_lruvec(folio)`.
- `lru_gen_refault()`, recent means the shadow's sequence is within
  `MAX_NR_GENS` of `max_seq`; it never calls `folio_set_active()`.
- `lru_gen_refault()`, recent with workingset bit: `folio_set_workingset()`
  and `WORKINGSET_RESTORE_BASE`; `WORKINGSET_ACTIVATE_BASE` only if
  `lru_gen_in_fault()`.
- `lru_gen_refault()`, recent without workingset bit: restores the stored
  refs into the folio flags under `LRU_REFS_MASK`.
- Call sites: two, `filemap_add_folio()` (skipped with `__GFP_WRITE`) and
  `__swap_cache_alloc()` in `mm/swap_state.c`; both run before
  `folio_add_lru()`.
