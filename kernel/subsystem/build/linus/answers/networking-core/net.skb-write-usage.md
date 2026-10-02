- `ip_rcv()`: does not call `skb_share_check()` itself; `ip_rcv_core()` in
  `net/ipv4/ip_input.c` does.
- `iptunnel_handle_offloads()`: calls `skb_header_unclone()`, and only for a GSO
  buffer. It reserves no headroom.
- A queued buffer can be shared: `__skb_try_recv_from_queue()` takes a
  reference for `MSG_PEEK` and leaves the buffer on the queue.
- **Potentially unsafe usage**: changing `struct sk_buff` fields while
  `skb_shared()` is true.
  - Unsafe: when the change is still there after the function returns, or the
    buffer is queued. The other holder sees the new `data` and `len`.
  - Safe: after `skb_share_check()`, on the pointer it returns, as
    `ip_rcv_core()` does.
  - Safe: when `data` and `len` are put back before returning, as `packet_rcv()`
    does. The other holder is the caller of `deliver_skb()`, which does not run
    until the handler returns.
- **Potentially unsafe usage**: writing packet bytes while `skb_cloned()` is
  true.
  - Unsafe: when `skb_clone_writable()` is false for the range. A tap's clone or
    the original in a retransmit queue holds the same bytes.
  - Safe: when `skb_ensure_writable()` has returned 0 for the range. It skips the
    copy if `skb_clone_writable()` holds. `nf_nat_ipv4_manip_pkt()` and
    `__skb_vlan_pop()` do this.
- **Potentially unsafe usage**: writing a GSO field of
  `struct skb_shared_info`, such as `gso_type`, on a clone.
  - Unsafe: when `skb_header_cloned()` is true. The other clone uses the same
    `struct skb_shared_info`.
  - Safe: after `skb_header_unclone()`, as `iptunnel_handle_offloads()` does
    before it sets bits in `gso_type`.
- **Potentially unsafe usage**: writing into page fragments in place.
  - Unsafe: when `skb_cloned()` or `skb_has_shared_frag()` is true. Another
    buffer or user space holds the same pages.
  - Unsafe: when only `skb_cloned()` was tested. `pskb_copy()` and
    `skb_unclone()` leave pages shared by reference with `skb_cloned()` false.
  - Safe: after `skb_cow_data()`, which leaves no page frags and copies
    `frag_list` members that are shared or cloned.
