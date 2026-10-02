- `genlmsg_multicast_allns()`: has no test of `netnsok`.
- `genlmsg_multicast_allns()` locking: `genlmsg_mcast()` takes
  `rcu_read_lock()` itself and clones with `GFP_ATOMIC`. The kerneldoc in
  `include/net/genetlink.h` says the caller must hold RTNL or RCU;
  `genl_ctrl_event()` calls it without taking either.
- `genlmsg_multicast_allns()` return: 0 only if some netns took the message
  and none failed. An error other than `-ESRCH` from any netns is returned
  even after an earlier delivery. `-ESRCH` if nobody listened.
- `genlmsg_multicast_netns()` and `genlmsg_multicast()`: also reach a socket
  in another netns that set `NETLINK_LISTEN_ALL_NSID`, if that netns has an
  id for the sending net and the socket's opener has `CAP_NET_BROADCAST` in
  the user namespace of the sending net; see `do_one_broadcast()` in
  `net/netlink/af_netlink.c`.
- `genl_has_listeners()`: the listener bitmap is per protocol, in
  `nl_table`, not per netns. `net` only supplies the kernel socket. A
  non-zero result can come from a socket in any netns.
- `genl_has_listeners()` with `group >= n_mcgrps`: returns `-EINVAL`, which
  is non-zero, so a caller that tests the result as a boolean goes on to
  build the message.
