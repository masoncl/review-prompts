- `skb_dst_force()` return value: `skb->_skb_refdst != 0UL`.

| skb state on entry | Returns | skb dst afterwards |
|---|---|---|
| no dst | false | none |
| counted dst | true | unchanged |
| noref dst, `dst_hold_safe()` succeeds | true | counted |
| noref dst, `dst_hold_safe()` fails | false | cleared |

- A false return covers both "no dst" and "hold failed": callers that accept
  an skb with no dst test `skb_dst(skb)` first, as `__nf_queue()` and
  `xfrm_trans_queue_net()` do; callers that need a dst test `skb_dst(skb)`
  afterwards, as `ip_route_input()`, `xfrm_input()` and `xfrm_output_one()`
  do.
- `ip_route_input_noref()`: attaches a noref dst only on a hit in the nexthop
  input cache (`nhc_rth_input`, or `fnhe_rth_input` of a nexthop exception);
  otherwise `ip_route_input_slow()`, `__mkroute_input()` and
  `ip_route_input_mc()` attach a counted dst with `skb_dst_set()`.
- `ip_route_input_noref()`: drops its own `rcu_read_lock()` before it
  returns; the caller's RCU section is what keeps a noref result valid.
- `__copy_skb_header()` in `net/core/skbuff.c`: uses `skb_dst_copy()`, which
  copies the noref bit and takes no reference for a noref dst; a clone or
  copy is not an upgrade.
- Upgrade points: search for `skb_dst_force(`; the tree has under twenty
  callers. Most ignore the return value.
  - `__dev_queue_xmit()`: before the qdisc is looked up, so for queueless
    devices too; with `IFF_XMIT_DST_RELEASE` it calls `skb_dst_drop()`
    instead.
  - `dev_loopback_xmit()` and `loopback_xmit()`: before `netif_rx()` and
    `__netif_rx()`.
  - `__neigh_event_send()`: before the skb goes on `neigh->arp_queue`.
  - `__sock_queue_rcv_skb()`, `sock_queue_err_skb()`, `__sk_add_backlog()`.
  - `__nf_queue()` and `xfrm_trans_queue_net()`: fail with `-ENETDOWN` and
    `-EHOSTUNREACH` when the hold fails.
- TCP receive: `tcp_add_backlog()` calls `tcp_cleanup_skb()`, which calls
  `skb_dst_drop()`; the skb reaches `sk_add_backlog()` with no dst.
- IPv4 UDP and raw receive: `ipv4_pktinfo_prepare()` with `drop_dst` true
  drops the dst; `__udp_enqueue_schedule_skb()` neither drops nor forces.
- `__release_sock()`: has
  `DEBUG_NET_WARN_ON_ONCE(skb_dst_is_noref(skb))` for every backlog skb.
- **Potentially unsafe usage**: dereferencing `skb_dst(skb)` after an upgrade
  point without a NULL test.
  - Unsafe: when the skb could have carried a noref dst into
    `skb_dst_force()` and the caller ignored the return value; a failed hold
    leaves `skb_dst()` NULL.
  - Safe: the dst was counted before the upgrade point (attached with
    `skb_dst_set()`, as `ip_route_input_mc()` does), since `skb_dst_force()`
    acts only when `skb_dst_is_noref()` is true.
  - Safe: the code tests `skb_dst(skb)` after the force, as
    `ip_route_input()` in `include/net/route.h` does.
- **Potentially unsafe usage**: putting an skb on a list that is processed
  after `rcu_read_unlock()` while `skb_dst_is_noref()` is true.
  - Unsafe: when nothing else holds a reference on the dst until the list is
    processed; the last `dst_release()` frees the entry after one grace
    period.
  - Safe: call `skb_dst_force()` inside the RCU section first, as
    `__neigh_event_send()` does before `__skb_queue_tail()`.
  - Safe: call `skb_dst_drop()` first when the consumer needs no route, as
    `tcp_cleanup_skb()` does.
  - Safe: the owner of the dst keeps its own reference for as long as such
    skbs can exist, as `mtk_poll_rx()` in
    `drivers/net/ethernet/mediatek/mtk_eth_soc.c` relies on: the driver holds
    the reference from `metadata_dst_alloc()` until `mtk_free_dev()`.
