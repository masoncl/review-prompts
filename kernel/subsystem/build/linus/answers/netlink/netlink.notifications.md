- `info->nlhdr` may be NULL: `nlmsg_report()` in `include/net/netlink.h`
  returns 0 for NULL, and `genl_notify()` then only multicasts.
- Requester and the multicast: excluded only when echo is set. Without echo
  `nlmsg_notify()` passes 0 as the port to skip, so a requester that joined
  the group gets the multicast copy.
- Required of `info`: `genl_info_net(info)` must be a valid net;
  `genl_notify()` dereferences it for `genl_sock`.
- `genl_info_init_ntf()`: leaves the net unset. Under `CONFIG_NET_NS`
  `genl_info_net()` then returns NULL; without it `read_pnet()` returns
  `&init_net`.
- **Unsafe usage**: passing a `struct genl_info` set up by
  `genl_info_init_ntf()` to `genl_notify()` without `genl_info_net_set()`.
  - Safe: pass the `struct genl_info` the core gave the handler, as
    `ovs_notify()` in `net/openvswitch/datapath.c` does; the core sets the
    net with `genl_info_net_set()` in `genl_family_rcv_msg_doit()`.
