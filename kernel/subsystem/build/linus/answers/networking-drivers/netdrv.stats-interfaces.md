- Rows that differ from the usual picture:

| Counters | Fed by | Read through |
|---|---|---|
| Per-queue | `struct netdev_stat_ops` in `dev->stat_ops` | `NETDEV_CMD_QSTATS_GET`, dump only |
| PHY device group, string "phydev" in `stats_std_names` | `get_phy_stats` in `struct phy_driver`; no `struct ethtool_ops` callback | `ETHTOOL_MSG_STATS_GET`, group `ETHTOOL_STATS_PHY` |
| Link down events | `link_down_events` in `struct phy_device`, then `get_link_stats` in `struct phy_driver`, then `get_link_ext_stats` in `struct ethtool_ops` | `ETHTOOL_MSG_LINKSTATE_GET` |
| Timestamping | `get_ts_stats` | `ETHTOOL_MSG_TSINFO_GET` |
| MAC merge | `get_mm_stats` | `ETHTOOL_MSG_MM_GET` |
| Page pool | none; the core reads the pool | `NETDEV_CMD_PAGE_POOL_STATS_GET`, only with `CONFIG_PAGE_POOL_STATS` |

- `ETHTOOL_MSG_STATS_GET` carries five groups only: eth-phy, eth-mac,
  eth-ctrl, rmon, phydev; see `stats_prepare_data()` in
  `net/ethtool/stats.c`.
- `get_phy_stats` of the PHY driver: is passed both the eth-phy and the
  phydev structs, runs before `get_eth_phy_stats`, and runs only when the
  source is `ETHTOOL_MAC_STATS_SRC_AGGREGATE`.
- `get_link_ext_stats` of the MAC driver: runs after the PHY path, so a value
  it writes replaces what `__phy_ethtool_get_link_ext_stats()` stored.
- `get_pause_stats`: never called if the driver lacks `get_pauseparam`;
  `pause_prepare_data()` returns `-EOPNOTSUPP` first.
- `get_fec_stats`: called only after `get_fecparam` exists and returned 0;
  see `fec_prepare_data()`.
- `get_mm_stats`: called only after `get_mm` exists and returned 0; see
  `mm_prepare_data()`.
- `page_pool_ethtool_stats_get_count()`,
  `page_pool_ethtool_stats_get_strings()`, `page_pool_ethtool_stats_get()`
  and `page_pool_get_stats()`: marked deprecated in
  `include/net/page_pool/helpers.h` and `net/core/page_pool.c`.
- `page_pool_get_stats()`: adds into the caller's struct; the caller zeroes
  it first.
- Page pool netlink visibility: only a pool created with a netdev
  (`pool->slow.netdev`) is linked by `page_pool_list()`; any other pool gets
  `-ENOENT` in `netdev_nl_page_pool_get_do()` and is skipped by dumps.
