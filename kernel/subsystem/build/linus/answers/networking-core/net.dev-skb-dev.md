- `__sock_queue_rcv_skb()` and `__sk_receive_skb()` in `net/core/sock.c`: set
  `skb->dev` to NULL before queueing; `sock_queue_rcv_skb_reason()` goes
  through the first.
- `tcp_v4_rcv()`: sets `skb->dev` to NULL after `process:`, before
  `tcp_v4_do_rcv()` or `tcp_add_backlog()`; TCP does not use `dev_scratch`.
- `dev_scratch`: used only by UDP (`net/ipv4/udp.c`, `include/net/udp.h`); on
  a UDP receive queue the field is not a pointer.
- A fragment on a reassembly queue: `skb->dev` is not cleared; for a fragment
  linked into the rb-tree it is overwritten by `rbnode`, which shares its
  storage, so reading it yields rb-tree data, not a device.
- `ip_frag_queue()`: copies `skb->dev` to a local before
  `inet_frag_queue_insert()` and saves `dev->ifindex` in `qp->iif`.
- `ip_frag_reasm()`: sets `skb->dev` to the device of the fragment that
  completed the datagram; it does no ifindex lookup.
- `ip_expire()`: the only place in `net/ipv4/ip_fragment.c` that uses
  `dev_get_by_index_rcu()` with `qp->iif`; it first takes the head out of the
  tree with `inet_frag_pull_head()`.
- `flush_all_backlogs()`: runs in `unregister_netdevice_many_notify()` after
  `reg_state` becomes `NETREG_UNREGISTERING` and before the first
  `synchronize_net()`.
- `flush_backlog()`: drops only buffers on `input_pkt_queue` and
  `process_queue` whose `skb->dev->reg_state` is `NETREG_UNREGISTERING`; a
  buffer on any other queue is not found by `flush_backlog()`.
