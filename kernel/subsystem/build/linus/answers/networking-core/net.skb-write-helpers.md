- `skb_cow_head()` success: no other holder counts the header part, so headers
  in front of the payload may be rewritten as well as pushed.
  `__vlan_insert_inner_tag()` in `include/linux/if_vlan.h` moves the MAC header
  after it.
- `skb_cow_head()`: the payload may still be shared with payload-only holders.
  It makes no test against `hdr_len`; `skb_clone_writable()`, used by
  `skb_ensure_writable()`, does.
- `skb_cow_data()`: pulls every page frag into the head whenever
  `nr_frags` is not 0, cloned or not. It fails with `-ENOMEM` when
  `__pskb_pull_tail()` refuses unreadable frags.
- `skb_ensure_writable_head_tail()` in `net/core/skbuff.c`: takes the skb and a
  `struct net_device`, and reallocates when the buffer is cloned or short of
  `needed_headroom` or `needed_tailroom`. It pulls nothing. `dsa_user_xmit()`
  uses it.
- `skb_expand_head()` in `net/core/skbuff.c`: grows headroom on transmit for a
  buffer that may be shared. It clones a shared buffer, keeps `sk` on the
  replacement, and frees the buffer and returns NULL on failure.
  `ip_finish_output2()` uses it.
