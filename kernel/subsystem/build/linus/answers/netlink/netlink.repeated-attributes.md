- `struct nla_policy` and `lib/nlattr.c` have no multi-attribute notion;
  `tb[type]` is the last instance for every policy.
- Parse with a policy: every instance passes `validate_nla()` during the
  parse, so a later walk over the same stream reads validated attributes.
- `genlmsg_data()` and `genlmsg_len()`: skip only `GENL_HDRLEN`; they are the
  right walk bounds only for a family whose `hdrsize` is 0.
- Family with a user header: walk with `nlmsg_for_each_attr()` and pass
  `GENL_HDRLEN` plus `hdrsize` as the header length.
- Top-level walk, for example: `dpll_pin_set_from_nlattr()` in
  `drivers/dpll/dpll_netlink.c`, `netdev_nl_read_rxq_bitmap()` in
  `net/core/netdev-genl.c`, `br_vlan_rtm_process()` in `net/bridge/br_vlan.c`.
- Walk inside a nest, for example: `br_afspec()` in
  `net/bridge/br_netlink.c`.
- More users: search for `nla_for_each_attr_type`,
  `nlmsg_for_each_attr_type` and `nla_for_each_nested_type`.
