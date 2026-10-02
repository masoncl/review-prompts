- Reader context: `u64_stats_fetch_begin()` and `u64_stats_fetch_retry()` hold
  nothing across the loop; they neither disable nor assert preemption, so the
  body may be preempted or interrupted.
- `seqcount_lockdep_reader_access()`: on 32-bit under
  `CONFIG_DEBUG_LOCK_ALLOC` it saves and restores interrupts inside
  `u64_stats_fetch_begin()` only, not across the body.
- **Potentially unsafe usage**: `+=` inside the fetch loop body.
  - Unsafe: when the code can be built for 32-bit and the left-hand side
    holds a value from before this pass, such as a running total over queues
    or CPUs; a retry adds the same counters again.
  - Safe: when the same pass assigns the variable with `=` first, as
    `bnge_get_ring_stats64()` in
    `drivers/net/ethernet/broadcom/bnge/bnge_netdev.c` does; the totals are
    added after the loop.
  - Safe: when the code is built for 64-bit only, as `hinic3_get_stats64()` in
    `drivers/net/ethernet/huawei/hinic3/hinic3_netdev_ops.c`, whose
    `CONFIG_HINIC3` depends on `CONFIG_64BIT`; `__u64_stats_fetch_retry()`
    returns `false` there, so the loop never retries.
- `u64_stats_copy()`: makes no fetch call itself and belongs inside the loop,
  copying into a local struct; `br_multicast_get_stats()` in
  `net/bridge/br_multicast.c` and `vxlan_vnifilter_stats_get()` in
  `drivers/net/vxlan/vxlan_vnifilter.c` sum per-CPU stats this way.
- There is no ip_tunnel_get_stats64() in this tree; `dev_get_tstats64()` in
  `net/core/dev.c` does that job through `dev_fetch_sw_netstats()`.
- `netdev_stats_to_stats64()`: not a u64_stats reader; it reads the
  `atomic_long_t` fields of `struct net_device_stats` with
  `atomic_long_read()` and uses no `struct u64_stats_sync`.
- `dev_fetch_dstats()` in `net/core/dev.c`: `static`; drivers reach it only
  through `dev_get_stats()` when `dev->pcpu_stat_type` is
  `NETDEV_PCPU_STAT_DSTATS` and the driver sets neither `ndo_get_stats64` nor
  `ndo_get_stats`.
