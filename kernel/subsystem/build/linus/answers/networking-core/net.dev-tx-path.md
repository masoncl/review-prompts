- No-queue path in `__dev_queue_xmit()`: `dev_xmit_recursion()` check, then
  `validate_xmit_skb()`, then `HARD_TX_LOCK()`; validation is outside the
  transmit lock on this path too.
- Recursion test on the no-queue path: `netif_tx_owned()`, not an open-coded
  compare of `xmit_lock_owner`; under `CONFIG_PREEMPT_RT` it tests the
  rt-mutex owner instead.
- `validate_xmit_skb()` first step: `validate_xmit_unreadable_skb()`, which
  frees a buffer with unreadable frags that the device cannot send.
- `validate_xmit_skb()`: segmentation and the linearize/checksum pair are
  alternatives; a buffer that `netif_needs_gso()` is segmented and skips
  `__skb_linearize()` and `skb_csum_hwoffload_help()` in this function.
- `validate_xmit_skb()` results: the buffer, NULL (freed; `tx_dropped`
  counted on the drop paths of `validate_xmit_skb()` itself), or
  `ERR_PTR(-EINPROGRESS)` when async xfrm crypto took it.
- **Unsafe usage**: testing the result of `validate_xmit_skb()` with `!skb`
  only; `ERR_PTR(-EINPROGRESS)` is then dereferenced.
  - Safe: `IS_ERR_OR_NULL()`, as `validate_xmit_skb_list()` and
    `__dev_queue_xmit()` do; the latter returns `NET_XMIT_SUCCESS` for
    `-EINPROGRESS`.
  - Safe: a NULL test on the result of `validate_xmit_skb_list()`, as
    `sch_direct_xmit()` does; that function skips `IS_ERR_OR_NULL()` entries
    and never returns an error pointer.
- Requeued buffers: `dequeue_skb()` clears `*validate` for `q->gso_skb`
  entries but sets it again when `xfrm_offload()` is non-NULL.
- `qdisc_pkt_len_segs_init()`: runs before `rcu_read_lock_bh()` and both
  egress hooks; on a bad GSO header `__dev_queue_xmit()` frees the buffer and
  returns `-EINVAL`.
- Locked qdisc in `__dev_xmit_skb()`: buffers are pushed on the lockless
  `q->defer_list`; the CPU that found the list empty takes the root lock and
  enqueues the whole list. `struct Qdisc` has no busylock field.
- `xmit_one()` tests `dev_nit_active_rcu()`; `dev_nit_active()` is the wrapper
  that takes `rcu_read_lock()` itself.
- Present in this tree, not gone: `netdev_pick_tx()` (called by
  `netdev_core_pick_tx()` when the driver has no `ndo_select_queue`) and
  `dev_queue_xmit_accel()` (inline in `include/linux/netdevice.h`).

| Name not in this tree | What does the job |
|---|---|
| dev_gso_segment | `skb_gso_segment()` called from `validate_xmit_skb()` |
| qdisc_pkt_len_init | `qdisc_pkt_len_segs_init()` |
| NETIF_F_LLTX | `lltx` bit in `struct net_device`, tested by `HARD_TX_LOCK()` |
| skb->xmit_more | `netdev_xmit_more()` |
| NETDEV_TX_LOCKED | nothing; `enum netdev_tx` has `NETDEV_TX_OK` and `NETDEV_TX_BUSY` |
| Qdisc busylock | `defer_list` and `defer_count` in `struct Qdisc` |
