- `SKB_GSO_DODGY` on transmit: enforced by `net_gso_ok()` through
  `skb_gso_ok()` in `netif_needs_gso()`; `gso_features_check()` does not test
  the bit.
- Devices that set `NETIF_F_GSO_ROBUST` (search `drivers/net/`; for example
  `drivers/net/virtio_net.c`): when `netif_needs_gso()` is false they receive
  the buffer with `SKB_GSO_DODGY` still set and no `gso_segment` callback run.
- `qdisc_pkt_len_segs_init()`: called from `__dev_queue_xmit()` for every
  buffer; for `SKB_GSO_DODGY` it recomputes `gso_segs`, and a bad header drops
  the buffer with `SKB_DROP_REASON_SKB_BAD_GSO`.
- NULL return: produced by `tcp_gso_segment()`, `__udp_gso_segment()` and
  `sctp_gso_segment()` when `skb_gso_ok(skb, features | NETIF_F_GSO_ROBUST)`;
  they do not test `SKB_GSO_DODGY`, so a buffer without the bit that passes
  `skb_gso_ok()` also gets NULL and a recomputed `gso_segs`.
- `inet_gso_segment()`: makes no such test; it passes NULL through and
  restores `skb->network_header`.
- Other `SKB_GSO_DODGY` handling, found by searching the name: for example
  `dev_gro_receive()` flushes such a buffer, `tcp4_gso_segment()` refuses
  `skb_segment_list()` for it, and `__pskb_pull_tail()` sets the bit.
- `__skb_gso_segment()`: never frees the original buffer, on any return; the
  caller frees it on error and after a list is returned.
- Returned list: its head can be the original buffer; `skb_segment_list()`
  returns it after `skb_get()`. Release the original with `consume_skb()`,
  as `validate_xmit_skb()` does, never by assuming it is distinct.
- `__skb_gso_segment()`: calls `skb_reset_mac_header()` and
  `skb_reset_mac_len()` itself; the caller does not have to.
- `features` containing `NETIF_F_GSO_PARTIAL`: `__skb_gso_segment()` then
  dereferences `skb->dev`.
