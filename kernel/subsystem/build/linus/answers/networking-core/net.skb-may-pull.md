- Unreadable frags: `__pskb_pull_tail()` returns NULL first when
  `!skb_frags_readable(skb)`; `pskb_may_pull_reason()` reports this as
  `SKB_DROP_REASON_NOMEM`.
- `SKB_DROP_REASON_NOMEM` covers every NULL from `__pskb_pull_tail()`:
  `pskb_expand_head()` failing (allocation or `skb_orphan_frags()`),
  `skb_clone()` of a shared `frag_list` member, `pskb_pull()` on a
  `frag_list` member.
- Copy from frags: not a failure return. `__pskb_pull_tail()` wraps
  `skb_copy_bits()` in `BUG_ON()`.
- `pskb_inet_may_pull()` with a `skb->protocol` other than `ETH_P_IP` or
  `ETH_P_IPV6`: uses length 0, which still pulls `skb_network_offset(skb)`
  bytes and can fail.
- `pskb_inet_may_pull()` without `CONFIG_IPV6`: the `ETH_P_IPV6` case is
  compiled out, so an IPv6 skb gets length 0.
- `skb_vlan_inet_prepare()` in `include/net/ip_tunnels.h`: the variant for
  skbs that may carry VLAN tags. It pulls MAC plus base IP header from
  `skb->data` and sets the network header itself.
