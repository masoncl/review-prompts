- `NLM_F_CAPPED` and TLVs: independent; `netlink_ack()` appends the TLVs
  after the echoed payload when there is one, after the request header when
  capped.
- `NLMSGERR_ATTR_POLICY`: not emitted for a policy type that
  `__netlink_policy_dump_write_attr()` in `net/netlink/policy.c` skips, for
  example `NLA_REJECT` and `NLA_UNSPEC`.
- `NLMSG_DONE` TLVs: `netlink_dump_done()` uses `netlink_ack_tlv_len()` and
  `netlink_ack_tlv_fill()` with `nlk->dump_done_errno`, so a failed dump
  carries the offset, policy and missing-attribute TLVs too, and a
  successful one only message and cookie.
- Condition for `NLMSG_DONE` to carry anything: the extack is a zeroed local
  of `netlink_dump()`, so only what the `->dump()` call of the same
  `netlink_dump()` invocation set is sent.
- Extack set by a `->dump()` call that returns a positive value, or
  `-EMSGSIZE` with data in the skb: discarded.
- No tailroom for `NLMSG_DONE` (header plus errno) in that skb: `NLMSG_DONE`
  is built by the next `netlink_dump()` call, which does not call `->dump()`
  again, so the errno arrives without TLVs.
- `RTNL_FLAG_DUMP_SPLIT_NLM_DONE`: `rtnl_dumpit()` in `net/core/rtnetlink.c`
  returns `skb->len` for a final 0, so an extack set by a handler that
  returned 0 after writing data is not delivered.
- TLVs larger than the remaining `skb_tailroom()`: `netlink_dump_done()` sets
  `NLM_F_ACK_TLVS` and writes no TLVs.
- `->start()`: `cb->extack` is the `extack` member of
  `struct netlink_dump_control`, which `genl_family_rcv_msg_dumpit()` fills
  and `rtnetlink_rcv_msg()` leaves NULL.
- `->start()` that returns 0: its extack is dropped when the first
  `netlink_dump()` call returns 0, because `__netlink_dump_start()` then
  returns `-EINTR` and `netlink_rcv_skb()` sends no ACK.
