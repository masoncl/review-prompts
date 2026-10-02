- `DEV_CORE_STATS_INC()`: not callable; it generates four inline helpers and
  is `#undef`-ed right after in `include/linux/netdevice.h`.
- The helpers are `dev_core_stats_rx_dropped_inc()`,
  `dev_core_stats_tx_dropped_inc()`, `dev_core_stats_rx_nohandler_inc()` and
  `dev_core_stats_rx_otherhost_dropped_inc()`.
- Driver use of the helpers: present in the tree for the driver's own drops,
  for example `dev_core_stats_tx_dropped_inc()` in
  `drivers/net/ethernet/broadcom/bnxt/bnxt.c`; `netdev_core_stats_inc()` is
  exported.
- `dev->core_stats` itself: the kerneldoc of `struct net_device` says not to
  use the field in drivers; go through the helpers.
- **Potentially unsafe usage**: counting a drop in the driver's own
  `rx_dropped` or `tx_dropped`.
  - Unsafe: when the same drop is also counted in `dev->core_stats`, by the
    core or by a helper call; `dev_get_stats()` adds `dev->core_stats` to
    whatever the driver reports, so the drop shows twice.
  - Safe: when the drop is counted in one place only, as `vrf_xmit()` does
    for a transmit drop with `dev_dstats_tx_dropped()` on a
    `NETDEV_PCPU_STAT_DSTATS` device and no `dev->core_stats` helper call;
    `__dev_queue_xmit()` counts no drop when the transmit routine has
    consumed the skb.
