- Models take `nla_nest_end()` to be the only way to close a nest and to be
  unable to fail. It stores the length in the 16-bit `nla_len` and checks
  overflow only with `DEBUG_NET_WARN_ON_ONCE()`; `nla_nest_end_safe()` in
  `include/net/netlink.h` returns `-EMSGSIZE` past `U16_MAX`.
- Models do not know when per-socket private data dies. `netlink_release()`
  calls `genl_release()`, which runs `sock_priv_destroy`, before the `unbind`
  calls and before the `done` of an unfinished dump;
  `genl_unregister_family()` waits for `genl_sk_destructing_cnt` to reach 0.
- Models take a family to set `min_dump_alloc` in
  `struct netlink_dump_control`. `genl_family_rcv_msg_dumpit()` builds that
  struct itself and leaves the field 0; a Generic Netlink dumper can only
  raise `cb->min_dump_alloc`.
- Models expect `kmalloc_array()` and an explicit gfp argument in the core.
  `net/netlink/genetlink.c` uses `kmalloc_objs()`, `kmalloc_obj()` and
  `kzalloc_obj()` from `include/linux/slab.h`; `default_gfp()` supplies
  `GFP_KERNEL` when the argument is left out.
- Models do not know `nlmsg_payload()` in `include/net/netlink.h`: it returns
  the fixed header only if `nlmsg_len` covers the given size, else NULL.
- Models expect the classic socket-op signatures in
  `net/netlink/af_netlink.c`. `netlink_bind()` and `netlink_connect()` take
  `struct sockaddr_unsized *`, and `netlink_getsockopt()` takes `sockopt_t *`.
