- Stop helpers: `netif_txq_maybe_stop()` and, under it,
  `netif_txq_try_stop()`; there is no __netif_txq_maybe_stop() in this tree.
- `down_cond`: an argument of `__netif_txq_completed_wake()` only;
  `netif_txq_completed_wake()` takes five arguments and passes `false`.
- Stop-side barrier: `smp_mb__after_atomic()`, which relies on the `set_bit()`
  in `netif_tx_stop_queue()`.
- Wake-side barrier: comes from `netdev_txq_completed_mb()`, which issues
  none when `bytes` is 0, with or without `CONFIG_BQL`.
- `__netif_txq_completed_wake()` with `pkts == 0`: never wakes and returns -1,
  whatever `get_desc` says.
- Ring indexes: the macros require no particular representation; `get_desc`
  is any expression, and the example in
  `Documentation/networking/driver.rst` masks the index difference.
- Stop side, context: it re-enables with `netif_tx_start_queue()`, which does
  not reschedule the qdisc, so outside the transmit routine the queue can end
  up enabled but not run.
- Wake side, context: no context restriction; the DOC comment in
  `include/net/netdev_queues.h` assumes that no two wake attempts for one
  queue run concurrently.
- False wake-ups: not prevented, says the same DOC comment; the transmit
  routine must still test for a full ring at its start.
- Return values: 0 means the stop or wake happened; 1 means nothing was
  done (the queue was left enabled, was already enabled, or `down_cond` held);
  -1 means the stop raced and was undone, or the wake threshold was not
  reached.
- BQL: the wake macros report completion through
  `netdev_tx_completed_queue()`, so the driver must not report the same bytes
  again; the stop macros report nothing, and the driver calls
  `netdev_tx_sent_queue()` itself.
- `__ixgbe_maybe_stop_tx()`: calls `netif_subqueue_try_stop()`; it is not
  open-coded here.
- bnxt: the `__netif_txq_completed_wake()` call is in `__bnxt_tx_int()`.
