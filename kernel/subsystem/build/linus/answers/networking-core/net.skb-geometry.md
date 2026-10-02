- `pskb_may_pull_reason()`: reports `SKB_DROP_REASON_PKT_TOO_SMALL` when
  `len > skb->len`, and `SKB_DROP_REASON_NOMEM` for every
  `__pskb_pull_tail()` failure, whatever its cause.
- **Potentially unsafe usage**: `pskb_may_pull()` on an skb that may be
  shared (`skb->users` above 1).
  - Unsafe: when the head has to be reallocated (not enough tailroom for the
    pulled bytes, or `skb_cloned()`); `pskb_expand_head()` does
    `BUG_ON(skb_shared(skb))`.
  - Safe: after `skb_share_check()`, as `ip_rcv_core()` in
    `net/ipv4/ip_input.c` does before its first `pskb_may_pull()`.
- **Potentially unsafe usage**: `skb_header_pointer()` with an offset that
  can be negative.
  - Unsafe: when nothing limits the offset to the headroom;
    `__skb_header_pointer()` tests only `hlen - offset >= len`, so it returns
    `skb->data + offset` with no test against `skb->head`.
  - Safe: `skb_header_pointer_careful()`, which returns NULL when
    `-offset > skb_headroom(skb)`, as `u32_classify()` in
    `net/sched/cls_u32.c` does.
  - Safe: an offset built from `skb_mac_offset()`, which is
    `skb->head + skb->mac_header - skb->data` and so never points before
    `skb->head`, as `vlan_get_tci()` in `net/packet/af_packet.c` does.
- `skb_pointer_if_linear()`: returns `skb->data + offset` or NULL, with no
  copy and no pull; it rejects a negative offset through its unsigned compare.
