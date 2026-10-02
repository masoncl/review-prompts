- Kernel socket: `sk_alloc()` takes a passive reference with
  `net_passive_inc()` and a tracker in `net->notrefcnt_tracker`.
  `__sk_destruct()` drops both.
- Unclosed kernel socket after teardown: `struct net` and `net->gen` stay
  allocated, so `sock_net(sk)` can be dereferenced. Per-net state is gone,
  including the `net_generic()` areas freed by `ops_free_list()`.
- `sk_clone()`: the clone inherits `sk_net_refcnt`. A child of a kernel listener
  takes only `net_passive_inc()`.
- `sk_net_refcnt_upgrade()`: drops the tracker and the passive reference first,
  then calls `get_net_track()` and `sock_inuse_add()`.
- `sk_net_refcnt`: assigned only by `sk_alloc()` and `sk_net_refcnt_upgrade()`.
  `sock_create_kern()` always passes `kern` 1, and `net/socket.c` has no
  creation helper that takes the main count for a kernel socket.
- **Potentially unsafe usage**: calling `sk_net_refcnt_upgrade()` on a kernel
  socket.
  - Unsafe: when nothing guarantees the main count is nonzero. It calls
    `get_net_track()`, which increments without a test.
  - Safe: bracketed by a successful `maybe_get_net()` and a `put_net()`, as
    `rds_tcp_tune()` in `net/rds/tcp.c` does. It returns false on NULL.
  - Safe: when the caller holds a main reference of its own across the call,
    as `generic_ip_connect()` in `fs/smb/client/connect.c` does through the
    `get_net()` that `cifs_get_tcp_session()` stored in the server.
- `sk_net_refcnt_upgrade()` context: it passes `GFP_KERNEL` to the tracker
  allocation, so call it where sleeping is allowed.
- Upgraded socket closed only from a pernet exit handler: its reference keeps
  the main count above zero, so `cleanup_net()` never runs that handler for
  the namespace. `__put_net()` is the only path that queues `cleanup_net()`,
  and it runs only when the main count reaches zero.
