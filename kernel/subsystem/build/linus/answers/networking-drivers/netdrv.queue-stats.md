- Queue-count change: drivers are encouraged to reset the per-queue counters
  (comment on `struct netdev_stat_ops` in `include/net/netdev_queues.h`).
- Device-scope totals: count events since the last explicit reset of the
  device; a reconfiguration such as a change of queue count is not a reset
  (`Documentation/netlink/specs/netdev.yaml`).
- Two in-tree patterns satisfy this: `bnxt_get_base_stats()` returns totals
  saved from torn-down rings; `virtnet_get_base_stats()` keeps per-queue
  counters and sums the inactive queues with `netdev_stat_queue_sum()`.
- `get_base_stats()` also selects the device-scope fields: a field it leaves
  unset is not reported even if every queue sets it; see
  `netdev_nl_stats_add()` in `net/core/netdev-genl.c`.
- `get_base_stats()` writing 0: valid, and needed to get a field reported
  when there is no history.
- No `get_base_stats()`: `netdev_nl_stats_by_netdev()` reports nothing for
  the device; device scope is the default scope of the dump.
- A per-queue field left unset by one queue: skipped in the device sum, the
  field is still reported.
- Device scope on a down device: `get_base_stats()` and the per-queue
  callbacks still run for every index below `real_num_rx_queues` and
  `real_num_tx_queues`; `bnxt_get_queue_stats_rx()` guards for this.
- `netdev_stat_queue_sum()` called by a driver: can pass the per-queue
  callbacks an index at or above the real queue count.
