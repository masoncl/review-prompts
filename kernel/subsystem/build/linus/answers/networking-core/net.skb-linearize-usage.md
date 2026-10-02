- `skb_header_pointer()` in `include/linux/skbuff.h`: read-only alternative.
  Offset counts from `skb->data`; returns a pointer into the head when the
  bytes are linear, else copies to the caller's buffer; NULL when short.
- Transmit paths need the pull too: a tunnel `ndo_start_xmit` handler cannot
  assume the inner IP header is linear. `ipgre_xmit()` in
  `net/ipv4/ip_gre.c` calls `pskb_inet_may_pull()` first.
- **Potentially unsafe usage**: dereferencing `ip_hdr(skb)` with no pull in
  the same function.
  - Unsafe: when some path to this point has no earlier function that pulled
    that header.
  - Safe: when an earlier function on the path pulled it; `udp_rcv()` reads
    `ip_hdr(skb)->saddr` after `ip_rcv_core()` pulled `iph->ihl*4`.
