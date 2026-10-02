- **Potentially unsafe usage**: reading or freeing the buffer after
  `dev_queue_xmit()` or `netif_rx()` returns.
  - Unsafe: when the caller holds no reference of its own. Every path of
    `__dev_queue_xmit()` and `enqueue_to_backlog()` in `net/core/dev.c`
    consumes the buffer, whatever the return value: it is queued, handed to
    the driver or a hook, or freed.
  - Safe: copy the value before the call and use only the copy, as
    `vlan_dev_hard_start_xmit()` in `net/8021q/vlan_dev.c`,
    `macvlan_start_xmit()` in `drivers/net/macvlan.c` and `loopback_xmit()` in
    `drivers/net/loopback.c` do with `len = skb->len`.
  - Safe: when the caller raised `skb->users` before the call, as
    `pktgen_xmit()` in `net/core/pktgen.c` does under `F_SHARED` around
    `dev_queue_xmit()`, `netif_receive_skb()` and `netdev_start_xmit()`.
    `kfree_skb_reason()` and `consume_skb()` drop one reference through
    `skb_unref()`.
  - Safe: after a callee that can refuse the buffer, when its return value
    says so, as in `veth_xmit()`, which touches the buffer only after
    `veth_forward_skb()` returned `NETDEV_TX_BUSY`; that value comes only from
    `veth_xdp_rx()`, when `ptr_ring_produce()` failed. `dev_queue_xmit()` and
    `netif_rx()` have no such value.
- `macvlan_queue_xmit()`: saves nothing. The saved length is in its caller,
  `macvlan_start_xmit()`, and is `skb->len` with no `ETH_HLEN` added.
- `iptunnel_xmit()` in `net/ipv4/ip_tunnel_core.c` and `ip6tunnel_xmit()` in
  `include/net/ip6_tunnel.h`: compute `pkt_len` themselves before
  `ip_local_out()` or `ip6_local_out()`, so a tunnel driver that calls them
  does not save the length.
- `ip_finish_output2()` and `neigh_resolve_output()`: save no length; they
  return the result of the transmit call and do not touch the buffer again.
- `pktgen_xmit()`: accounts bytes from `pkt_dev->last_pkt_size`, saved when
  the buffer was built.
- pktgen on a device without `IFF_TX_SKB_SHARING`: `clone_skb` above 0, and
  `burst` above 1 in `M_START_XMIT` mode, are refused with `-EOPNOTSUPP`.
