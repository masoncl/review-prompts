- `xs_connect()`: moves `XPRT_LOCKED` from the task to the transport pointer
  with `xprt_lock_connect()`, so the lock outlives the
  `xprt_release_write()` at the end of `xprt_connect()`; the worker ends with
  `xprt_unlock_connect()`.
- `XPRT_CONNECTING` on TCP: `xs_tcp_setup_socket()` does not clear it when
  `kernel_connect()` returns 0, `-EINPROGRESS` or `-EALREADY`;
  `xs_tcp_state_change()` clears it on `TCP_ESTABLISHED`, or on `TCP_CLOSE` if
  `XPRT_SOCK_CONNECTING` was set.
- Backoff: `xs_connect()` calls `xprt_reconnect_backoff()` when it schedules
  the attempt, before the outcome is known, and only if `transport->sock` is
  set.
- `reestablish_timeout` set to 0: `xs_data_ready()` on any incoming data,
  `xs_close()`, `xs_tcp_state_change()` on `TCP_FIN_WAIT1`; for RDMA
  `rpcrdma_reply_handler()` and `xprt_rdma_close()`.
- `reestablish_timeout` raised to at least the initial value:
  `xs_tcp_state_change()` on `TCP_CLOSE_WAIT` and `TCP_CLOSING`,
  `xs_tcp_setup_socket()` once the SYN is sent, `rpcrdma_xprt_connect()` after
  `rdma_connect()`.
- `TCP_ESTABLISHED` and `TCP_LAST_ACK`: do not touch `reestablish_timeout`.
- `max_reconnect_timeout`: `to_maxval` of the transport's timeout, or
  `args->reconnect_timeout` in `xs_setup_tcp()`; after setup it can only be
  lowered, by the `set_connect_timeout` method
  (`xs_tcp_set_connect_timeout()`, `xprt_rdma_set_connect_timeout()`). No
  XS_TCP_MAX_REEST_TO exists here.
- AF_LOCAL: `xs_local_connect()` connects synchronously, without
  `xprt_lock_connect()` or the backoff helpers; an async task gets
  `-ENOTCONN`, and a failed connect sleeps 15 s unless the task is soft-connect.
- RPC/RDMA: `xprt_rdma_connect()` queues its worker on `system_dfl_long_wq`,
  not `xprtiod_workqueue`, and delays only if `re_connect_status` is non-zero.
- `connect_cookie` is bumped in more places than `xs_tcp_state_change()`:
  search for it; `xprt_autoclose()` and `xs_sock_reset_connection_flags()`
  are the ones to remember.
- `rq_connect_cookie`: starts at the current cookie minus one in
  `xprt_request_init()`, so a freshly initialised request never matches the
  current cookie.
- The cookie is not checked when a reply is received; replies are matched by
  XID alone, and `xprt_wake_pending_tasks()` does not look at it.
- `xprt_rdma_send_request()`: drops the connection rather than resend a
  request whose `rq_connect_cookie` equals the current cookie.
- `xprt_force_disconnect()` on one request's error is used in the tree on
  purpose: `xprt_rdma_timer()` calls it on a retransmit timeout.
