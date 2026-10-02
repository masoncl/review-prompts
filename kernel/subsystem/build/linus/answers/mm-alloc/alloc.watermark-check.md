- Highatomic term: `__zone_watermark_unusable_free()` subtracts
  `z->nr_free_highatomic`, not `nr_reserved_highatomic`.
- Highatomic term is skipped when any bit of `ALLOC_RESERVES` is set, so also
  for `ALLOC_NON_BLOCK` alone.
- CMA term: `zone_page_state(z, NR_FREE_CMA_PAGES)` under `CONFIG_CMA` when
  `ALLOC_CMA` is clear; `struct zone` has no free-CMA field.
- `NR_UNACCEPTED`: not subtracted by the test. Unaccepted pages are counted in
  `NR_FREE_PAGES`; `cond_accept_memory()` subtracts them in its own
  calculation.
- There is no ALLOC_HIGH flag; `__GFP_HIGH` maps to `ALLOC_MIN_RESERVE`.
- Lowering steps, each applied to the already lowered value:

  | Flags set | Mark becomes about |
  |---|---|
  | `ALLOC_MIN_RESERVE` | 1/2 |
  | `ALLOC_MIN_RESERVE` and `ALLOC_NON_BLOCK` | 3/8 |
  | `ALLOC_OOM` | half of whatever the rows above left |
  | `ALLOC_NON_BLOCK` alone | unchanged |
  | `ALLOC_HIGHATOMIC` alone | unchanged |

- `ALLOC_NO_WATERMARKS`: `get_page_from_freelist()` still runs the test; the
  flag only overrides a failed result, after `cond_accept_memory()` and
  `_deferred_grow_zone()` have been tried.
- Without `CONFIG_MMU`, `ALLOC_OOM` is defined as `ALLOC_NO_WATERMARKS` in
  `mm/page_alloc.h`.
- Order above zero: a free area counts if any list below `MIGRATE_PCPTYPES`
  is non-empty, or `MIGRATE_CMA` with `ALLOC_CMA`, or `MIGRATE_HIGHATOMIC`
  with `ALLOC_HIGHATOMIC` or `ALLOC_OOM`.
- Order above zero: the request's own migratetype is not an input to the
  scan.
