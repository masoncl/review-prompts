| Function | `LRU_REFS_FLAGS` | `PG_workingset` | Other flag written |
|---|---|---|---|
| `folio_update_gen()`, when it writes the generation | clears | sets | none |
| `folio_inc_gen()` | clears | keeps | none |
| `lru_gen_add_folio()` | keeps | keeps | clears `PG_active` |
| `lru_gen_del_folio()` | keeps | keeps | may set `PG_active` |

- `folio_inc_gen()`: takes `lruvec` and `folio` only; there is no
  `reclaiming` argument and it does not touch `PG_reclaim`.
- `folio_inc_gen()`: takes the old generation from `lrugen->min_seq[type]`,
  not from the folio; a folio whose generation differs is returned unchanged.
- `folio_inc_gen()` callers: `sort_folio()` and `inc_min_seq()`; the second
  runs from `inc_max_seq()` when a type already has `MAX_NR_GENS`
  generations.
- `lru_gen_folio_seq()`: picks the generation from `PG_active`,
  `PG_workingset`, `PG_referenced`, `PG_reclaim`, dirty, writeback and
  swapcache, so kept access bits change where a re-added folio lands.
- **Unsafe usage**: reading `folio_lru_refs()` or the tier after
  `folio_inc_gen()` to account `protected[]`.
  - Safe: read refs and `PG_workingset` first, as `sort_folio()` and
    `inc_min_seq()` do.
- **Potentially unsafe usage**: re-adding a folio with `lru_gen_add_folio()`
  to change its generation.
  - Unsafe: when the caller expects a given generation and leaves stale
    `PG_active`, `PG_referenced`, `PG_workingset` or `PG_reclaim`;
    `lru_gen_folio_seq()` reads them.
  - Safe: clear `PG_referenced`, `LRU_REFS_MASK` and `PG_workingset` with
    `lru_gen_clear_refs()` while the folio is still on its generation list,
    as `deactivate_file_folio()` does before it queues the folio; once the
    generation bits are cleared `lru_gen_clear_refs()` returns without
    clearing anything.
  - Safe: `lruvec_add_folio_tail()` passes `reclaiming` true, which selects
    the oldest generation once `PG_active` is clear, as `lru_move_tail()`
    does.
  - Safe: set `PG_active` and clear `LRU_REFS_FLAGS` so that the folio lands
    in one of the two youngest generations, as `evict_folios()` does for
    rejects that would land in the oldest one.
