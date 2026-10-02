- `src` in `struct ethtool_eth_phy_stats`, `struct ethtool_eth_mac_stats`,
  `struct ethtool_eth_ctrl_stats`, `struct ethtool_rmon_stats` and
  `struct ethtool_pause_stats`: an input the core sets after the fill, not a
  counter; it names the MAC to report.
- Per-queue sentinel: `NETDEV_STAT_NOT_SET`, private to
  `net/core/netdev-genl.c`; same value as `ETHTOOL_STAT_NOT_SET`.
- `stats_prepare_data()` in `net/ethtool/stats.c`: fills its five structs
  with `memset()` of 0xff, not `ethtool_stats_init()`; the result is the
  same.
- Per-queue callback that sets no field at all: the core drops the whole
  entry for that queue; see `netdev_nl_stats_queue()`.
