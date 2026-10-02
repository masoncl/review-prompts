- Lock: `genl_bind()` and `genl_unbind()` hold `cb_lock` for read only;
  `genl_mutex` is not held.
- Capability flags: `GENL_MCAST_CAP_NET_ADMIN` and `GENL_MCAST_CAP_SYS_ADMIN`,
  tested with `ns_capable(net->user_ns, ...)` on the current task; on
  `-EPERM` `bind` is not called.
- `netnsok`: `genl_bind()` does not test it; `bind` runs for a join from any
  netns, and gets no net argument.
- Calls are not balanced. `netlink_setsockopt()` calls `bind` on every
  `NETLINK_ADD_MEMBERSHIP`, member already or not, and `unbind` on every
  `NETLINK_DROP_MEMBERSHIP`, member or not.
- `netlink_bind()`: calls `bind` for every bit set in `nl_groups`, including
  groups already joined.
- `netlink_undo_bind()`: on failure calls `unbind` for each requested
  lower-numbered group, including groups the socket had joined earlier and
  still holds.
- A later `bind(2)` with a smaller `nl_groups`: `netlink_bind()` overwrites
  the low 32 group bits; no `unbind` call for the groups dropped.
- Family unregister: `genl_unregister_mc_groups()` removes members with
  `__netlink_clear_multicast_users()`; no `unbind` call.
- In-tree user: only `thermal_genl_family` in
  `drivers/thermal/thermal_netlink.c` sets the callbacks.
