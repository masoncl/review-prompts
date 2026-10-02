- `boost_watermark()` caller: only `try_to_claim_block()` in
  `mm/page_alloc.c`; there is no steal_suitable_fallback() in this tree.
- Trigger: a fallback claim from a free page smaller than `pageblock_order`.
  `try_to_claim_block()` returns before the boost for larger pages, and
  boosts before it knows whether the block will be claimed.
- `__rmqueue_steal()`: takes a single fallback page and never boosts.
- `boost_watermark()` returns `false` and leaves the boost alone when
  `watermark_boost_factor` is 0, when the zone has fewer than
  `4 * pageblock_nr_pages` managed pages, or when the cap computed from the
  stored `_watermark[WMARK_HIGH]` is 0.
- `boost_watermark()` at the cap: still returns `true`, so the flag below is
  set although the boost did not grow.
- `boost_watermark()` wakes nothing. `try_to_claim_block()` sets
  `ZONE_BOOSTED_WATERMARK` when it returned `true` and `ALLOC_KSWAPD` is set;
  `rmqueue()`, not `get_page_from_freelist()`, tests and clears the bit and
  calls `wakeup_kswapd()`.
- `wakeup_kswapd()`: wakes kswapd for a node that `pgdat_balanced()` accepts
  if `pgdat_watermark_boosted()` finds a boosted zone, unless
  `kswapd_test_hopeless()`.
- `zone->watermark_boost` has three writers: `boost_watermark()`,
  `balance_pgdat()` and `__setup_per_zone_wmarks()`.
- `balance_pgdat()` does not zero the boost: it subtracts the per-zone value
  it saved in `zone_boosts[]` on entry, so boosts added during the pass
  remain.
- `balance_pgdat()` subtracts at the end of every pass that began with a
  boost, also when boost reclaim was abandoned because the node was
  unbalanced or reclaim made no progress.
- Gap between levels in `__setup_per_zone_wmarks()`: the floor is a quarter of
  the zone's proportional share of `min_free_kbytes`, not of the stored min;
  the two differ for highmem and `ZONE_MOVABLE`, whose stored min is clamped.
- Direct reads of `_watermark[]` in `mm/page_alloc.c` are unboosted reads:
  the cap in `boost_watermark()`, the mark in `__isolate_free_page()`, and
  the retry in `zone_watermark_fast()`.
