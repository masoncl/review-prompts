- `__release_sock()`: not private to `release_sock()`; `__sk_flush_backlog()` in
  `net/core/sock.c` and `__tcp_close()` in `net/ipv4/tcp.c` call it too.
- `__sk_flush_backlog()` and `__tcp_close()`: drain the backlog and leave
  `sk->sk_lock.owned` set, so backlog processing can change socket state in the
  middle of an owner's critical section.
- `sk_flush_backlog()` in `include/net/sock.h`: the inline that calls
  `__sk_flush_backlog()` when `sk->sk_backlog.tail` is set.
