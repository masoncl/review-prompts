- Busy on a no-queue device: `__dev_queue_xmit()` returns `-ENETDOWN`, not
  `NET_XMIT_DROP`; it frees with `kfree_skb_list_reason()` and counts
  `tx_dropped`.
- Busy on a no-queue device after segmentation (`is_list`): the unsent
  segments are freed the same way but the return value is `NETDEV_TX_OK`.
- Stopped queue on a no-queue device: same free, count and `-ENETDOWN`,
  without the driver being called (`netif_xmit_stopped()`).
- `-ENETDOWN`: `__dev_queue_xmit()` sets it in two places, both on the
  no-queue path (busy or stopped queue, and recursion).
- Deactivated device: `dev_deactivate_queue()` installs `noop_qdisc`, and
  `noop_enqueue()` drops the buffer and returns `NET_XMIT_CN`.
- NET_XMIT_POLICED is not defined; the qdisc codes are `NET_XMIT_SUCCESS`,
  `NET_XMIT_DROP` and `NET_XMIT_CN`.
- `dev_requeue_skb()`: calls `__netif_schedule()` only for a locked qdisc;
  for `TCQ_F_NOLOCK` it sets `__QDISC_STATE_MISSED` instead.
- A requeue does not prove the driver returned `NETDEV_TX_BUSY`:
  `sch_direct_xmit()` requeues without calling the driver when
  `netif_xmit_frozen_or_stopped()`, and `dev_hard_start_xmit()` sets
  `NETDEV_TX_BUSY` itself when the queue stops with segments left.
- `NET_XMIT_SUCCESS` on a locked qdisc: `__dev_xmit_skb()` returns it as soon
  as the buffer is on a non-empty `q->defer_list`, before any enqueue.
- Enqueue result on a locked qdisc: the CPU that flushes the list returns it
  only when it enqueued exactly one buffer; otherwise `NET_XMIT_SUCCESS`.
- `NET_XMIT_DROP` from `__dev_xmit_skb()` also covers a `defer_list` longer
  than `net_hotdata.qdisc_max_burst` and a qdisc with
  `__QDISC_STATE_DEACTIVATED`.
