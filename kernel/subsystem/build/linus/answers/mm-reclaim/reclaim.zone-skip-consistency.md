- `for_each_managed_zone_pgdat()`: defined in `include/linux/swap.h`.
- After the loop `zone` and `idx` point one past the bound and must not be
  used.
- Direction: the macro walks upward from index 0; code that needs the highest
  managed zone open-codes a downward loop with `managed_zone()`, as the
  `buffer_heads_over_limit` scan in `balance_pgdat()` does.
- **Unsafe usage**: a zone loop that answers "not balanced" or "throttle"
  when it visited no zone.
  - Safe: `pgdat_balanced()` returns true when `mark` is still `-1`, that is,
    no managed zone at or below `highest_zoneidx`.
  - Safe: `allow_direct_reclaim()` returns true when `pfmemalloc_reserve` is 0;
    `throttle_direct_reclaim()` waits on `pfmemalloc_wait` for it to return
    true.
- `allow_direct_reclaim()` skips a managed zone only if
  `zone_reclaimable_pages()` is 0 and the `NR_FREE_PAGES` snapshot is
  non-zero.
- A zone with nothing reclaimable and nothing free still adds its
  `min_wmark_pages()` to the reserve in `allow_direct_reclaim()`.
- `allow_direct_reclaim()` bound: `ZONE_NORMAL`, fixed.
- `allow_direct_reclaim()` when the test fails and kswapd is on
  `kswapd_wait`: lowers `kswapd_highest_zoneidx` to `ZONE_NORMAL` if it was
  higher, then wakes kswapd.
- `balance_pgdat()`: passes `highest_zoneidx` to `pgdat_balanced()`, not
  `sc.reclaim_idx`, which `buffer_heads_over_limit` may have raised.
- `kswapd_shrink_node()`: sums `sc->nr_to_reclaim` up to `sc->reclaim_idx`.
- `should_abort_scan()` (MGLRU): open-codes the loop with `managed_zone()`
  and needs every managed zone to pass; no zone visited means abort.
