- `netdev_tx_completed_queue()`: ignores `pkts`; only `bytes` has to balance.
- `netdev_tx_completed_queue()` with `bytes == 0`: returns before
  `dql_completed()` and before its `smp_mb()`.
- Balance at every instant: `dql_completed()` in
  `lib/dynamic_queue_limits.c` has `BUG_ON(count > num_queued -
  dql->num_completed)` on each call, so bytes must be reported sent before
  the completion handler can report them.
- `dql_queued()` with `count > DQL_MAX_OBJECT`: `WARN_ON_ONCE()` and the bytes
  are not counted, so completing them later breaks the balance.
- `netdev_tx_sent_queue()`: returns void; the doorbell decision comes from
  `__netdev_tx_sent_queue()`.
- `__netdev_tx_sent_queue()` with `xmit_more` true: only counts the bytes,
  does not set `__QUEUE_STATE_STACK_XOFF`, and returns
  `netif_tx_queue_stopped()`.
- `__netdev_tx_sent_queue()` without `CONFIG_BQL`: still returns that value,
  or `true` when `xmit_more` is false.
- Core and reset: nothing under `net/` calls `netdev_tx_reset_queue()`;
  `dql_init()` runs once, in `netdev_init_one_queue()`, so BQL state survives
  `ndo_stop` and `ndo_open` unless the driver resets it.
- **Unsafe usage**: `netdev_tx_reset_queue()` while transmit or completion for
  that queue can still run, or a completion report afterwards for packets
  queued before it; `dql_reset()` zeroes `num_queued` and `num_completed`
  with no lock, so the `BUG_ON()` in `dql_completed()` can fire.
  - Safe: stop transmit and NAPI first, then free the ring without reporting
    completion, then reset; `ixgbe_down()` calls `netif_tx_disable()` and
    `ixgbe_napi_disable_all()` before `ixgbe_clean_all_tx_rings()`.
