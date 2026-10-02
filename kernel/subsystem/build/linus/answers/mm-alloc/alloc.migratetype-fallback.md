- There is no __rmqueue_fallback() and no move_freepages_block_isolate()
  here. `__rmqueue()` calls `__rmqueue_claim()`, then `__rmqueue_steal()`.
- `find_suitable_fallback()`: returns `enum fallback_result`
  (`FALLBACK_FOUND`, `FALLBACK_EMPTY`, `FALLBACK_NOCLAIM`, in
  `mm/page_alloc.h`), not a type. The type comes back through `mt_out`,
  which may be NULL.
- `should_try_claim_block()`: receives the order of the candidate free page,
  not the order requested.
- `FALLBACK_NOCLAIM`: ends the downward scan in `__rmqueue_claim()`.
- Movable requests: a claim is tried only when the candidate page is at
  least `pageblock_order / 2` or `page_group_by_mobility_disabled` is set;
  smaller candidates are left to `__rmqueue_steal()`.
- `try_to_claim_block()` returning NULL (too few free or alike pages, or the
  block straddles a zone): `__rmqueue_claim()` tries the next lower order.
- `__rmqueue_steal()`: runs only after the whole claim scan found nothing,
  and only without `ALLOC_NOFRAGMENT`. In the `rmqueue_bulk()` loop, a
  `*mode` of `RMQUEUE_STEAL` makes later calls skip the scan.
- `ALLOC_NOFRAGMENT`: 0 without `CONFIG_ZONE_DMA32`, so there the raised
  `min_order` in `__rmqueue_claim()` and the steal skip never apply.
- Steal remainder: `page_del_and_expand()` gets `fallback_mt`, so the split
  remainder returns to the lists of the block's own type.
- Claim of a page >= `pageblock_order`: `del_page_from_free_list()` with
  `block_type`, then `change_pageblock_range()`, then `expand()` with
  `start_type`. A change must keep that order; see "Pageblock flags".
- Claim of a smaller page: `__move_freepages_block()`, then
  `set_pageblock_migratetype()`, then `__rmqueue_smallest()` on the new type,
  so the page returned need not be the candidate.
