- `NLM_F_DUMP_INTR` is not sticky: `nl_dump_check_consistent()` overwrites
  `cb->prev_seq` on every call, so only the first message checked after the
  counter changed carries the flag; user space has to test every message.
- `NLMSG_DONE` is checked too: `netlink_dump_done()` calls
  `nl_dump_check_consistent()` on it, so the flag can appear on a message the
  dumper never built.
- Counter names: there is no genl_ctrl_seq here; `fib_seq` is the FIB
  notifier's counter (for example `net/ipv4/fib_notifier.c`) and is never
  assigned to `cb->seq`. Search for assignments to `cb->seq` to find the
  dump counters.
- A value built from several counters can be 0 even if none of them is:
  `inet_base_seq()` in `net/ipv4/devinet.c` adds two and substitutes
  `0x80000000` for a 0 sum.
- Other ways in-tree code keeps the value non-zero, for example:
  `dev_base_seq_inc()` in `net/core/dev.c` replaces a wrapped 0 with 1;
  `net/batman-adv/` stores `generation << 1 | 1`.
- Writing 0 to both `cb->seq` and `cb->prev_seq` is the reset used when one
  dump moves on to an independent set, as `rtnl_dump_all()` and
  `rtnl_mdb_dump()` do; it is not a counter value.
