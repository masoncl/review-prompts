- Socket creators other than `kernel_accept()` in `svc_tcp_accept()`, all
  through `__sock_create()` with `kern` = 1: `xs_create_sock()`,
  `xs_local_setup_socket()`, `svc_create_socket()`, and `rpc_sockname()` in
  `net/sunrpc/clnt.c`.
- Code under `net/sunrpc/` does not call `sock_create_kern()`.
- RDMA: `rpcrdma_create_id()` on the client; on the server
  `svc_rdma_create()` calls `svc_rdma_create_listen_id()`, which calls
  `rdma_create_id()`.
- `svc_rdma_listen_handler()`: on `RDMA_CM_EVENT_ADDR_CHANGE` it creates a
  new listener id with the transport's `xpt_net`.
- `__rdma_create_id()` in `drivers/infiniband/core/cma.c`: takes its own
  `get_net()`, so a `struct rdma_cm_id` pins its namespace; a kernel socket
  does not unless `sk_net_refcnt_upgrade()` was called on it.
- `sk_alloc()`: sets `sk_net_refcnt` to 0 for a `kern` socket; the socket
  takes `net_passive_inc()` and no `get_net_track()` reference on its
  namespace.
- `xs_create_sock()` and `svc_create_socket()`: call
  `sk_net_refcnt_upgrade()` for `IPPROTO_TCP` only, so a TCP socket holds its
  own counted reference; UDP, `AF_LOCAL` and `rpc_sockname()` sockets are
  not upgraded.
- `sk_net_refcnt_upgrade()`: has `WARN_ON_ONCE(sk->sk_net_refcnt)`;
  `svc_addsock()` takes a user socket from `sockfd_lookup()` and does not
  call it.
- `svc_addsock()`: returns `-EINVAL` when `sock_net(so->sk) != net`.
- Client reference: `xprt_init()`, called from `xprt_alloc()`, takes
  `get_net_track()`; `xprt_free()` drops it. `xprt_create_transport()` does
  not touch `xprt_net`.
- `rpc_net_ns()`: reads `xprt_net` of `clnt->cl_xprt` inside
  `rcu_read_lock()` and returns it without taking a reference.
- There is no svc_create_xprt() and `struct svc_serv` has no namespace
  member; the namespace is the `net` argument of `svc_xprt_create()` or
  `svc_xprt_create_from_sa()`.
- Socket transports: `svc_udp_init()` and `svc_tcp_init()` pass
  `sock_net(svsk->sk_sock->sk)` to `svc_xprt_init()`, so `xpt_net` comes from
  the socket, for listeners, accepted sockets and `svc_addsock()` alike.
- `svc_xprt_destroy_all()`: takes `serv`, `net` and a third argument
  `unregister`.
- GSS members of `struct sunrpc_net`: `rsc_cache` and `rsi_cache` are set up
  by `gss_svc_init_net()` through `rpcsec_gss_net_ops`, which
  `init_rpcsec_gss()` registers, not by `sunrpc_init_net()`; `gssp_lock` is
  initialised by `sunrpc_init_net()`.
- `sunrpc_exit_net()`: has `WARN_ON_ONCE(!list_empty(&sn->all_clients))`;
  every client of the namespace must be gone before exit.
- No code under `net/sunrpc/` reads `current->nsproxy`; each namespace comes
  from an object or an argument, apart from `&init_net` in `proc_dodebug()`.
- **Potentially unsafe usage**: passing an uncounted `struct net *` to
  `__sock_create()` or `net_generic()`.
  - Unsafe: when the pointer was read from an object that can be replaced
    or freed meanwhile, and the caller holds no reference on that object or
    on the namespace.
  - Safe: `xprt->xprt_net` while the caller holds the `struct rpc_xprt`, as
    `xs_create_sock()` does; `xprt_init()` took the reference.
  - Safe: `get_net()` inside `rcu_read_lock()` before the call and
    `put_net()` after, as `rpc_localaddr()` does around `rpc_sockname()`;
    `rpc_switch_client_transport()` puts the old `cl_xprt` only after
    `synchronize_rcu()`.
  - Safe: `xprt->xpt_net` while the caller holds the `struct svc_xprt`, as
    `svcauth_unix_set_client()` does; `svc_xprt_init()` took the reference.
  - Safe: the `net` given to a pernet `init` or `exit` callback, as
    `ip_map_cache_create()` uses it.
  - Safe: `genl_info_net(info)` or `sock_net(skb->sk)` inside a netlink
    handler, as `sunrpc_nl_cache_flush_doit()` does.
- **Potentially unsafe usage**: storing a `struct net *` in a long-lived
  object without `get_net()` or `get_net_track()`.
  - Unsafe: when the object can outlive the namespace's pernet exit.
  - Safe: `cd->net` set by `cache_create_net()` for a cache that a pernet
    `init` creates and the matching `exit` destroys, as `sunrpc_init_net()`
    and `sunrpc_exit_net()` do for the `ip_map` and `unix_gid` caches.
  - Safe: `rqstp->rq_bc_net` set by `svc_process_bc()`; it is the
    `xprt_net` of `req->rq_xprt` and is used during that request only, while
    the request holds the `xprt_get()` from `xprt_enqueue_bc_request()`.
  - Safe: `gss_auth->net`, taken with `get_net_track()` in
    `net/sunrpc/auth_gss/auth_gss.c` and dropped with `put_net_track()`.
