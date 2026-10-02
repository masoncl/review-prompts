- Gate: `genl_header_check()` acts only when
  `hdr->cmd >= family->resv_start_op`. `GENL_DONT_VALIDATE_STRICT` plays no
  part.
- Order: `genl_family_rcv_msg()` calls it before the op lookup, so an
  unknown command at or above `resv_start_op` with a bad header gets
  `-EINVAL`, not `-EOPNOTSUPP`.
- Message length: not checked here. `genl_family_rcv_msg()` tests
  `nlmsg_len` against `nlmsg_msg_size()` of
  `GENL_HDRLEN + family->hdrsize` for every command.
- `nlmsg_flags`: `NLM_F_DUMP` is masked out only when both of its bits are
  set. Any bit left outside `NLM_F_REQUEST | NLM_F_ACK | NLM_F_ECHO` gives
  `-EINVAL`.
- `genlmsghdr.version`: not checked.
- `Documentation/userspace-api/netlink/intro.rst`, "Other
  request-type-specific flags": says only that these flags are "rarely used
  (and considered deprecated for new families)".
- The document gives no advice to use commands or attributes instead, and
  does not mention `resv_start_op`.
- Its per-type remarks: `NLM_F_ROOT` and `NLM_F_MATCH` are used only
  combined as `NLM_F_DUMP`; `NLM_F_ATOMIC` is never used; `NLM_F_NONREC` is
  used only by nftables and `NLM_F_BULK` only by some FDB operations; the
  NEW flags are the most used in classic Netlink and their meaning is
  unclear.
