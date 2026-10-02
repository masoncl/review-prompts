- Range check for `bad_attr` and `miss_nest`: `nlmsg_check_in_payload()` in
  `net/netlink/af_netlink.c` bounds the pointer by the one request message,
  from `nlmsg_data(nlh)` up to but excluding `nlh` plus `nlh->nlmsg_len`; it
  does not use the skb bounds.
- Pointer into another message of the same skb: fails the check.
- Failed check: `WARN_ON()` fires and only that offset TLV is skipped;
  message, `NLMSGERR_ATTR_POLICY` and `NLMSGERR_ATTR_MISS_TYPE` are still
  sent.
- **Unsafe usage**: `bad_attr` or `miss_nest` pointing at a
  `struct nlattr` outside the request message that is being acked.
  - Safe: a pointer from the attribute table parsed from the request `nlh`,
    as `genl_family_rcv_msg_attrs_parse()` produces; `nlmsg_check_in_payload()`
    defines the range.
- Message lifetime with the macros: not a concern; the literal forms store a
  `static` array and the `_FMT` forms store `_msg_buf`.
- Direct store to `_msg`: the string must live until `netlink_ack()` or
  `netlink_dump_done()` reads it with `strlen()`; `validate_nla()` in
  `lib/nlattr.c` stores `reject_message` of the policy entry for
  `NLA_REJECT`.
- **Unsafe usage**: copying a `struct netlink_ext_ack` by value after an
  `_FMT` macro set the message, then using the copy once the original is
  reused or gone; `_msg` of the copy points at `_msg_buf` of the original.
  - Safe: pass the same struct by pointer until the ACK is built, as
    `netlink_rcv_skb()` does with its local extack and `netlink_ack()`.
- Trailing newline in the message: flagged by
  `scripts/coccinelle/misc/newline_in_nl_msg.cocci`.
- `Documentation/userspace-api/netlink/intro.rst`, Extended ACK section: is
  addressed to user space and states no requirement on a family.
- What it tells user space: `NLMSGERR_ATTR_MSG` is a message in English
  describing the problem; `NLMSGERR_ATTR_OFFS` points to the attribute that
  caused the problem; an extended ACK on success is to be treated as a
  warning.
- Not in `intro.rst`: any rule about parsing the text, punctuation, or
  restating the errno.
