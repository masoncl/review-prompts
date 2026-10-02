- `netif_running()` inside `ndo_stop` called by the core: false;
  `__dev_close_many()` clears `__LINK_STATE_START` first.
- `netif_running()` inside `ndo_open`: true; `__dev_open()` sets the bit
  before the call and clears it if `ndo_open` fails.
- A driver that calls its own stop function sees `netif_running()` true;
  `__igb_shutdown()` calls `__igb_close()` only when it is true.
- `ndo_open` and `ndo_stop` run under the lock that
  `netdev_assert_locked_ops_compat()` asserts, which the ethtool ioctl and
  netlink handlers also hold (see "Ethtool callback locking"), so a
  `netif_running()` test in an ethtool op called from them is still
  serialised against open and close.
- Ethtool ops are gated on `netif_device_present()`, not on up: `-ENODEV` in
  `ethnl_ops_begin()` and `dev_ethtool_locked()`.
- `ndo_get_stats64`: called under `rcu_read_lock()` without rtnl, for example
  from `dev_seq_printf_stats()`; it cannot sleep or take a mutex.
- `ndo_set_rx_mode` on the inline path of `__dev_set_rx_mode()` (driver not
  ops-locked, no `ndo_set_rx_mode_async`, no `ndo_change_rx_flags`): gated on
  `IFF_UP`, which is still set while `ndo_stop` runs, and reachable without
  rtnl through `dev_mc_add()`; it can run concurrently with `ndo_stop`.
- `struct netdev_stat_ops`: `netdev_nl_stats_by_netdev()` calls
  `get_base_stats` and, through `netdev_stat_queue_sum()`, the per-queue
  callbacks with no `IFF_UP` test; only `netdev_nl_stats_by_queue()` tests it.
- `ndo_work`: `netdev_work_run()` tests `netif_device_present()` only.
- **Potentially unsafe usage**: `ndo_get_stats64` reading per-ring memory.
  - Unsafe: when `ndo_stop` frees the rings with nothing that makes the
    reader finish first; a `netif_running()` test alone does not.
  - Safe: ring pointers read with `READ_ONCE()` under `rcu_read_lock()` and
    freed with `kfree_rcu()`, as `ixgbe_get_stats64()` and
    `ixgbe_free_q_vector()` do.
  - Safe: a reader bit the close path waits on; `bnxt_get_stats64()` sets
    `BNXT_STATE_READ_STATS` before it tests `BNXT_STATE_OPEN`, and
    `__bnxt_close_nic()` clears `BNXT_STATE_OPEN` and then polls
    `bnxt_drv_busy()`.
