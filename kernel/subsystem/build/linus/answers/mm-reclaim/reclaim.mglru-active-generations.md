- `lru_gen_is_active()`: true for the generation of `max_seq` and of
  `max_seq - 1`, the two youngest; it does not read `min_seq[]`.
- Not statistics only: `lru_gen_del_folio()` with `reclaiming` false sets
  `PG_active` on a folio leaving an active generation.
- `set_initial_priority()` in `mm/vmscan.c` picks `sc->priority` from the
  node counters `NR_INACTIVE_FILE` and, when anon can be reclaimed,
  `NR_INACTIVE_ANON`; `lru_gen_update_size()` fills them according to
  `lru_gen_is_active()`.
- `inc_max_seq()`: moves the size of the `max_seq - 1` generation to inactive
  and the size of the `max_seq + 1` generation to active, as one delta.
- Active is relative to one lruvec's `max_seq`: `__lru_gen_reparent_memcg()`
  moves pages between the active and inactive counters when child and parent
  disagree on whether a generation index is active.
