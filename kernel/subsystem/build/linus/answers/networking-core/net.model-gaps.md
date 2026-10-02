- Models take `__dev_xmit_skb()` to enqueue under the qdisc root lock and
  return the enqueue result. For a qdisc without `TCQ_F_NOLOCK` it frees the
  buffer itself with `SKB_DROP_REASON_QDISC_BURST_DROP` when `q->defer_count`
  goes above `net_hotdata.qdisc_max_burst`.
- Models take an upper device's instance lock to order before a lower's.
  `netdev_lock_cmp_fn()` in `include/net/netdev_lock.h` accepts no order
  when RTNL is not held; lockdep consults it only for two locks of the same
  lock class.
- Models know only `ndo_set_rx_mode`. This tree adds
  `ndo_set_rx_mode_async` and `ndo_work`; `register_netdevice()` warns when
  an ops-locked driver has `ndo_set_rx_mode` without the async one.
- Models name icsk_retransmit_timer. It is not in this tree; the TCP
  retransmit timer is `tcp_retransmit_timer` in `struct sock`.
