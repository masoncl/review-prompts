- `Documentation/userspace-api/netlink/intro.rst`: contains no list of frozen
  properties and no list of permitted changes.
- Explicit freeze statements in the documents: "Answer requests" in
  `Documentation/core-api/netlink.rst` (reply versus ACK is uAPI), and
  `version` in `Documentation/userspace-api/netlink/genetlink-legacy.rst`
  ("compatibility breaking changes are generally not allowed").
- Family ID and multicast group ID: not fixed, except for the few families
  that `genl_register_family()` and `genl_validate_assign_mc_groups()` in
  `net/netlink/genetlink.c` special-case; otherwise the ID is allocated at
  registration, and user space resolves both by name through
  `CTRL_CMD_GETFAMILY`.
- `CTRL_ATTR_MAXATTR` in the `CTRL_CMD_GETFAMILY` reply: `ctrl_fill_info()`
  writes `family->maxattr`; a family that sets policy only per operation, for
  example the generated `netdev_nl_family` in `net/core/netdev-genl-gen.c`,
  reports 0.
- Per-operation attribute support: available only from `CTRL_CMD_GETPOLICY`
  for such a family.
- Probing by sending an attribute and reading the error: works only where the
  core validates strictly; `genl_family_rcv_msg_attrs_parse()` uses
  `NL_VALIDATE_LIBERAL` when the op sets `GENL_DONT_VALIDATE_STRICT`
  (`GENL_DONT_VALIDATE_DUMP_STRICT` for a dump), and parses nothing when the
  op has no policy.
- `version`: not a discovery mechanism;
  `Documentation/userspace-api/netlink/intro.rst` calls the header field
  irrelevant, and of the four schema files only
  `Documentation/netlink/genetlink-legacy.yaml` has a `version` property, so a
  `genetlink` spec always renders 1.
