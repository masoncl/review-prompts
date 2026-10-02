- Drop condition: `sc->order && sc->nr_reclaimed >= compact_gap(sc->order)`,
  tested after `shrink_node()` in every pass; `sc->nr_reclaimed` is the total
  for the whole `balance_pgdat()` run.
- The drop lasts for the run: `restart` resets `sc.priority` only, not
  `sc.order`.
- **Unsafe usage**: passing the `order` argument of `balance_pgdat()` to
  `pgdat_balanced()` after `kswapd_shrink_node()` has run.
  - Safe: pass `sc.order`, as the check at the top of the loop in
    `balance_pgdat()` does; `kswapd_shrink_node()` zeroes it so that later
    checks are at order 0.
  - Safe: pass the value `balance_pgdat()` returned, as `kswapd()` does with
    `reclaim_order` for `prepare_kswapd_sleep()`.
- `pgdat_balanced()` with `defrag_mode` and a non-zero order: compares
  `NR_FREE_PAGES_BLOCKS`, not `NR_FREE_PAGES`, with the watermark; after the
  drop it compares `NR_FREE_PAGES`.
- `kswapd()`: when `reclaim_order < alloc_order` it goes back to
  `kswapd_try_to_sleep()` without reading a new request; there `alloc_order`
  is used for `wakeup_kcompactd()` only.
