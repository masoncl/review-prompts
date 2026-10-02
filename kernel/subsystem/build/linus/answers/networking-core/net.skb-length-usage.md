- There is no __udp4_lib_rcv() here; `udp_rcv()` in `net/ipv4/udp.c` holds
  the `ulen > skb->len` and `ulen < sizeof(*uh)` checks.
- `ip_rcv_core()`: `ip_fast_csum()` runs after the `iph->ihl*4` pull and the
  reload, not before.
- `__tun_vnet_hdr_get()` in `drivers/net/tun_vnet.h`: where the user-supplied
  `hdr_len` is rejected when larger than `iov_iter_count(from)`.
- **Potentially unsafe usage**: `skb_pull()` or `__skb_pull()` with a wire
  length checked only against `skb->len`.
  - Unsafe: on a skb that may be nonlinear; `len > skb_headlen()` reaches the
    `BUG()` in `__skb_pull()`.
  - Safe: after `pskb_may_pull(skb, len)`, as `xfrm4_remove_beet_encap()` in
    `net/xfrm/xfrm_input.c` does before `__skb_pull(skb, phlen)`.
  - Safe: `pskb_pull()`, which calls `pskb_may_pull()` itself and returns
    NULL on failure.
- **Unsafe usage**: `skb_put()` with a length from a subtraction that can go
  negative.
  - Unsafe: with `NET_SKBUFF_DATA_USES_OFFSET` (`BITS_PER_LONG > 32`)
    `skb->tail` is `unsigned int`; `skb->tail += len` wraps backwards, so for
    a small negative value the `skb->tail > skb->end` test is false and
    `skb_over_panic()` is not called.
  - Safe: compare the operands before subtracting, as `mangle_contents()` in
    `net/netfilter/nf_nat_helper.c` does with `rep_len > match_len` before
    `skb_put(skb, rep_len - match_len)`.
