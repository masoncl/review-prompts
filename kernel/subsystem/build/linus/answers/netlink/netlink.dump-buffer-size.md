- `NLMSG_GOODSIZE`: `SKB_WITH_OVERHEAD(PAGE_SIZE)` only when `PAGE_SIZE` is
  below 8192, otherwise `SKB_WITH_OVERHEAD(8192UL)`; see
  `include/linux/netlink.h`.
- 32 KiB cap: applies only to `nlk->max_recvmsg_len`, in
  `netlink_recvmsg()`; `cb->min_dump_alloc` is not capped by
  `netlink_dump()`, for example `crypto/crypto_user.c` passes up to 65535.
- Tailroom the dumpit sees: exactly the size chosen, because `skb_reserve()`
  in `netlink_dump()` hides what the allocator rounded up.
- Receive buffer test: the skb is charged to `sk->sk_rmem_alloc` first; the
  round fails with `-ENOBUFS` only if something else was already charged and
  the total reaches `sk->sk_rcvbuf`, so one skb larger than `sk_rcvbuf`
  passes on an empty queue.
- Raising `cb->min_dump_alloc` during the dump: honoured, `netlink_dump()`
  reads it every round.
- Pattern for an object found too large: raise `cb->min_dump_alloc`, leave
  the skb empty, return a positive value; the next round retries with the
  larger skb, as `nl80211_dump_wiphy()` and `nl802154_dump_wpan_phy()` do.
- That retry round: user space reads a zero-length datagram, since
  `__netlink_sendskb()` queues the empty skb.
- Growing in the same round: `__inet_diag_dump()` in `net/ipv4/inet_diag.c`
  calls `pskb_expand_head()` on the empty skb and runs the handler again.
- rtnetlink: there is no calcit op in this tree; `rtnetlink_rcv_msg()` calls
  `rtnl_calcit()` directly and only for `RTM_GETLINK`, other rtnetlink dumps
  start with `min_dump_alloc` 0.
