- `cb->ctx`: `u8 ctx[NETLINK_CTX_SIZE]` (48) in an anonymous union with
  `long args[6]`; it has no alignment attribute of its own.
- `ctx` is the last member of `struct netlink_callback`, so an overrun lands
  in what follows `cb` in `struct netlink_sock`.
- Size check: `NL_ASSERT_CTX_FITS()` in `include/linux/netlink.h`; there is
  no NL_ASSERT_DUMP_CTX_FITS.
- The check is opt-in: nothing fails if a dumper casts `cb->ctx` without it;
  an open-coded `BUILD_BUG_ON(sizeof(*ctx) > sizeof(cb->ctx))` is the same
  check, for example in `net/ipv4/nexthop.c`.
- `struct genl_dumpit_info`: two members, `op` and an embedded
  `struct genl_info info`; the family is `info.family`.
- `genl_dumpit_info()` and `genl_info_dump()` return `const` pointers.
- `struct genl_info` of a dump: `genl_start()` sets every member; its own
  `ctx` / `user_ptr` union is zeroed and is not the dump position.
- `genl_info_dump(cb)->extack`: copied from `cb->extack` by `genl_start()`,
  by `genl_dumpit()` before each round and by `genl_done()`, so it has the
  values given under "Dump lifecycle", NULL in the family's `done`.
- Attribute release: `genl_done()` frees `attrs` and the
  `struct genl_dumpit_info`; there is no genl_parallel_done() here.
- `cb->data` under rtnetlink: holds the real handler whenever
  `rtnetlink_dump_start()` installs `rtnl_dumpit()`;
  `rtnetlink_dump_start()` warns if `control->data` was already set.
