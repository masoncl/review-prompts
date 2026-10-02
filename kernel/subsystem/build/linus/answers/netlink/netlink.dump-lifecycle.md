- Negative dumpit return: ends the dump and becomes the `int` payload of
  `NLMSG_DONE`; `sk->sk_err` is not touched and no `NLMSG_ERROR` is sent.
- `-EMSGSIZE` with `skb->len != 0`: rewritten to `skb->len`, so it means
  "more to come"; it ends the dump only when returned with an empty skb.
- `NLMSG_DONE` that does not fit: the skb goes out without it, and the next
  round writes only `NLMSG_DONE`; `cb->dump` is not called again, because it
  is called only while `nlk->dump_done_errno > 0`.
- `netlink_dump()` failing by itself in a round run from `netlink_recvmsg()`
  (`-ENOBUFS` on allocation failure or a full receive buffer):
  `netlink_recvmsg()` puts that in `sk->sk_err`; the dump stays running,
  `done` is not called, and a later read that dequeues a message can retry.
- Extack TLVs on `NLMSG_DONE`: gated by `NETLINK_F_EXT_ACK` on the socket in
  `netlink_ack_tlv_len()`; `NLM_F_ACK_TLVS` is the flag set on the result.
- `cb->extack` in `start`: `control->extack`, NULL when the caller of
  `netlink_dump_start()` set none; in `done`: NULL.
- `struct netlink_callback`: embedded in `struct netlink_sock` as `cb` and
  cleared with `memset()`, not allocated; it has no `start` member, only
  `struct netlink_dump_control` does.
- rtnetlink: `rtnl_dumpit()` in `net/core/rtnetlink.c` wraps the handler and
  takes `rtnl_lock()` unless `RTNL_FLAG_DUMP_UNLOCKED`.
- `RTNL_FLAG_DUMP_SPLIT_NLM_DONE`: `rtnl_dumpit()` turns a 0 return with data
  in the skb into `skb->len` and returns 0 on the next call without calling
  the handler, so `NLMSG_DONE` arrives in its own message.
