- `wakeup_kswapd()`: writes `kswapd_highest_zoneidx` and `kswapd_order` before
  it tests `waitqueue_active()`, so a request made while kswapd runs is kept
  for its next loop.
- `wakeup_kswapd()`: returns before recording anything only for an unmanaged
  zone or when `cpuset_zone_allowed()` fails.
- `wakeup_kswapd()` on a balanced node: skips the wake only if
  `pgdat_watermark_boosted()` is also false.
- `prepare_kswapd_sleep()`: wakes every `pfmemalloc_wait` sleeper first, before
  the hopeless and balance tests, on both calls.
- `allow_direct_reclaim()`: second waker; it calls
  `wake_up_interruptible(&pgdat->kswapd_wait)` directly when the reserve test
  fails, without going through `wakeup_kswapd()`.
- `wake_all_kswapds()`: with `defrag_mode` set, passes
  `max(order, pageblock_order)` as the order.
