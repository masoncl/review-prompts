- `skb_frag_t`: holds a `netmem_ref`, not a page pointer; it may refer to a
  `struct net_iov` (`include/net/netmem.h`), memory with no `struct page`.
- `struct dst_entry`: holds no neighbour; `ip_finish_output2()` in
  `net/ipv4/ip_output.c` looks up the `struct neighbour` per packet with
  `ip_neigh_for_gw()`, under `rcu_read_lock()`.
- `sk_backlog` in `struct sock`: not a `struct sk_buff_head`; a bare
  `head`/`tail` pair chained through `skb->next`, with no lock of its own.
  See `__sk_add_backlog()` in `include/net/sock.h`.
- `struct Qdisc` and `struct netdev_queue`: not one-to-one; a root qdisc
  whose ops have no `attach` is grafted onto every Tx queue of the device by
  `qdisc_graft()` in `net/sched/sch_api.c`, so the queues share it.
- `qdisc` and `qdisc_sleeping` in `struct netdev_queue`: both exist;
  `qdisc_sleeping` is the configured qdisc, `qdisc` is the one the transmit
  path uses and is `noop_qdisc` until `transition_one_qdisc()` activates it.
- `struct socket`: not always inside a `struct socket_alloc`;
  `struct tun_file` (`drivers/net/tun.c`) and `struct tap_queue`
  (`include/linux/if_tap.h`) embed one with no inode behind it.
- **Potentially unsafe usage**: `SOCK_INODE()` or `sock_init_data()` on a
  `struct socket`.
  - Unsafe: when the `struct socket` is embedded in a driver structure;
    `SOCK_INODE()` is a `container_of()` on `struct socket_alloc`, and
    `sock_init_data()` in `net/core/sock.c` calls it.
  - Safe: after `sock_from_file()` on `sock->file` returned that same socket,
    as `sock_read_xattr()` in `net/socket.c` tests first; `sock_from_file()`
    returns NULL unless `f_op` is `socket_file_ops`, which rejects tun and
    tap.
- `struct packet_type`: lives on one of five kinds of list, chosen by
  `ptype_head()` in `net/core/dev.c` from `type`, `dev` and `af_packet_net`:
  global `ptype_base[]`, or `ptype_all` / `ptype_specific` in `struct net` or
  in `struct net_device`.
- `list_func` in `struct packet_type`: called for a batch instead of `func`
  when set (`__netif_receive_skb_list_ptype()`); IPv4 and IPv6 set it to
  `ip_list_rcv()` and `ipv6_list_rcv()`, so a check added only to `ip_rcv()`
  misses batched packets.
- `udp4_lib_lookup()`: takes a reference; built only under
  `CONFIG_NF_TPROXY_IPV4` or `CONFIG_NF_SOCKET_IPV4`.
- `SOCK_RCU_FREE`: the flag that makes an unreferenced lookup result usable
  inside the RCU section; `sk_is_refcounted()` in `include/net/sock.h` tests
  it.
- `struct net_device` instance lock: mutex `lock`, taken after RTNL. On
  devices where `netdev_need_ops_lock()` (`include/net/netdev_lock.h`)
  returns true, `netdev_lock_ops()` takes it around driver callbacks; on
  other devices `netdev_lock_ops()` does nothing.
- `__dev_open()` in `net/core/dev.c`: asserts RTNL, then
  `netdev_assert_locked_ops_compat()`, so on an ops-locked device both locks
  are held around `ndo_open`.
