- `sk_add_backlog()`: the bound is the caller's `limit` argument, tested
  against `sk_backlog.len` plus `sk_rmem_alloc`; it has no limit of its own.
- `tcp_add_backlog()` limit: twice `sk_rcvbuf`, plus half of `sk_sndbuf`, plus
  64 KB, capped at `UINT_MAX`.
- `tcp_add_backlog()`: returns `enum skb_drop_reason`; on a non-zero return it
  has already called `bh_unlock_sock()`, so the caller must not unlock again.
- `tcp_add_backlog()` coalescing into `sk->sk_backlog.tail`: runs before the
  limit test and succeeds above the limit; it adds only the delta to
  `sk_backlog.len`.
- `sk_add_backlog()` returns `-ENOMEM`, not `-ENOBUFS`, for a pfmemalloc buffer
  on a socket without `SOCK_MEMALLOC`; `__sk_receive_skb()` and
  `tcp_add_backlog()` map it to `SKB_DROP_REASON_PFMEMALLOC` and `-ENOBUFS` to
  `SKB_DROP_REASON_SOCKET_BACKLOG`.
- `__sk_add_backlog()`: no limit test and no change to `sk_backlog.len`;
  `tcp_child_process()` uses it for an owned child socket.
- `TCP_LISTEN` socket in `tcp_v4_rcv()` and `tcp_v6_rcv()`: handed to
  `tcp_v4_do_rcv()` or `tcp_v6_do_rcv()` without `bh_lock_sock_nested()` and
  without a `sock_owned_by_user()` test.
- UDP receive in `net/ipv4/udp.c`: takes no `bh_lock_sock()` and has no
  backlog; `__udp_enqueue_schedule_skb()` pushes the buffer on the lockless
  `udp_prod_queue` list, and the producer that found that list empty moves the
  batch to `sk_receive_queue` under `sk->sk_receive_queue.lock`.
- Socket reference in softirq: not always held; `__inet_lookup()` returns a
  listener without a reference and sets `*refcounted` to false, and
  `tcp_v4_rcv()` calls `sock_put()` only when `refcounted` is true.
- `tcp_delack_timer()` when the socket is owned: takes `sock_hold()` only if
  it was the one to set `TCP_DELACK_TIMER_DEFERRED`; `tcp_release_cb()` drops
  that reference with `__sock_put()`.
