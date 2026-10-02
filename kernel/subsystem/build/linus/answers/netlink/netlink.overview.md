- `struct genl_split_ops`: both a table form a family supplies (`split_ops`
  in `struct genl_family`) and the form every lookup yields; see
  `genl_get_cmd()` in `net/netlink/genetlink.c`.
- More than one op table in one family: for example
  `net/wireless/nl80211.c` sets both `ops` and `small_ops`; what
  `genl_validate_ops()` requires of that is under "Operation table forms".
- Op pointer seen by `pre_doit` and `post_doit`, and `genl_dumpit_info(cb)->op`:
  a per-request copy with the reject-all policy and, for `ops` and
  `small_ops` entries, the family defaults filled in, not a pointer into the
  family's table.
- Generated code: the op form varies; `net/ipv4/fou_nl.c` generates
  `struct genl_small_ops`, `net/mptcp/mptcp_pm_gen.c` generates
  `struct genl_ops`, most others `struct genl_split_ops`.
- Generated file and `struct genl_family`: some define the family too
  (`net/core/netdev-genl-gen.c`); others hold only the tables and the family
  is hand-written elsewhere (`net/ipv4/fou_core.c`).
- Fixed family ids: `GENL_ID_CTRL`, `GENL_ID_VFS_DQUOT` and `GENL_ID_PMCRAID`;
  `genl_register_family()` picks the last two by comparing the family name.
- Multicast group numbers: allocated from one global bitmap (`mc_groups`), so
  a group has the same number in every netns; only the kernel socket
  `net->genl_sock`, and so delivery, is per netns, apart from listeners that
  set `NETLINK_LISTEN_ALL_NSID`.
- `genlmsg_multicast()`: sends through the `init_net` socket only; callers
  pass the index in the family's `mcgrps`, not the global number.
- `doit(skb, info)`: `skb` is the request; `skb->sk` is the kernel socket and
  the requester's socket is `NETLINK_CB(skb).sk`.
- `dumpit(skb, cb)`: `skb` is a new reply buffer owned by the requester's
  socket; the request is `cb->skb`, so sender data is `NETLINK_CB(cb->skb)`.
- `struct netlink_callback`: embedded in the requester's
  `struct netlink_sock`, found by portid in `__netlink_dump_start()`; it has
  no policy member.
- `struct genl_dumpit_info`: what `cb->data` is in a generic netlink dump;
  `genl_start()` allocates it and `genl_done()` frees it. It holds the op copy
  (with the dump's policy) and the dump's `struct genl_info`, read with
  `genl_info_dump()`. Family state goes in `cb->ctx`.
- `struct genl_info` for a do: on the stack of `genl_family_rcv_msg_doit()`;
  `attrs` is freed before that function returns, after `post_doit`.
- `attrs` entries: pointers into the request skb. For a dump
  `__netlink_dump_start()` holds a reference on that skb until the dump ends.
- `user_ptr` in `struct genl_info`: shares a union with
  `ctx[NETLINK_CTX_SIZE]`, zeroed before `pre_doit`; it is separate storage
  from `ctx` in `struct netlink_callback`.
- Notification `struct genl_info`: built by `genl_info_init_ntf()`, with
  `nlhdr` `NULL` and `genlhdr` pointing into its own `user_ptr[0]` storage,
  so `ctx` is not free for use; test with `genl_info_is_ntf()`.
- `struct netlink_ext_ack` for a request: one per message, zeroed on the stack
  of `netlink_rcv_skb()`.
- Extack TLVs reach userspace only if the requesting socket has
  `NETLINK_F_EXT_ACK` set; see `netlink_ack_tlv_len()`.
