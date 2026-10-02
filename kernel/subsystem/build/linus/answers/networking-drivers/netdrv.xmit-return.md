- `enum netdev_tx` in `include/linux/netdevice.h`: the only return values are
  `NETDEV_TX_OK` and `NETDEV_TX_BUSY`; NETDEV_TX_LOCKED is not defined.
- Any other value: `dev_xmit_complete()` treats every `rc < NET_XMIT_MASK` as
  consumed, which covers negative errno, `NET_XMIT_DROP` and `NET_XMIT_CN`.
- A value that fails `dev_xmit_complete()` and is not `NETDEV_TX_BUSY`:
  `sch_direct_xmit()` logs "BUG %s code %d qlen %d" and requeues the skb.
- After a drop: the value must pass `dev_xmit_complete()`; for example
  `ixgbe_xmit_frame_ring()` returns `NETDEV_TX_OK`, and `veth_xmit()` returns
  `NET_XMIT_DROP`.
- `NETDEV_TX_BUSY`: the caller keeps ownership, and what it does with the skb
  depends on the caller:

| Caller | On `NETDEV_TX_BUSY` |
|---|---|
| `sch_direct_xmit()` | requeues with `dev_requeue_skb()` |
| `__dev_queue_xmit()`, qdisc without `enqueue` | logs "Virtual device %s asks to queue packet!", frees the skb |
| `generic_xdp_tx()`, `dev_direct_xmit()` | `kfree_skb()` |
| `__netpoll_send_skb()` | retries, then queues to `npinfo->txq` |

- `veth_xmit()`: tests `qdisc_txq_has_no_queue()` and drops instead of
  returning `NETDEV_TX_BUSY`; when it does return it, it first restores the
  Ethernet header with `__skb_push()`.
- `Documentation/networking/driver.rst`, exception: `NETDEV_TX_BUSY` is "a hard
  error unless there is no way your device can tell ahead of time when its
  transmit function will become busy".
- `Documentation/networking/driver.rst`, example: on a full ring with the queue
  awake the transmit routine calls `netif_tx_stop_queue()`, `netdev_warn()`
  and returns `NETDEV_TX_BUSY`.
- `Documentation/networking/netdevices.rst` adds that on `NETDEV_TX_BUSY` the
  driver must not have put the skb in its DMA ring.
