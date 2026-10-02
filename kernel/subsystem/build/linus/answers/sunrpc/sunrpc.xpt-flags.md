- Bits that make a transport ready: the five that `svc_xprt_ready()` tests,
  `XPT_CONN`, `XPT_CLOSE`, `XPT_HANDSHAKE`, `XPT_DATA`, `XPT_DEFERRED`.
- `svc_handle_xprt()`: tests `XPT_CLOSE`, then `XPT_LISTENER`, then
  `XPT_HANDSHAKE`, and otherwise receives; it tests neither `XPT_CONN` nor
  `XPT_DATA`, so an `xpo_accept` or `xpo_recvfrom` that leaves its bit set
  with nothing pending is dequeued again at once.
- `XPT_CONN`: cleared by `xpo_accept`, not by `xpo_recvfrom`;
  `svc_tcp_accept()` sets it again after a successful accept,
  `svc_rdma_accept()` while `sc_accept_q` is not empty.
- `XPT_DATA` on RDMA: `svc_rdma_recvfrom()` clears it only when
  `sc_rq_dto_q` is empty; the socket methods clear it on entry and set it
  again if more may be queued.
- `XPT_KILL_TEMP`: a request, not a property; honoured only in the
  `XPT_CLOSE` branch of `svc_handle_xprt()`. `svc_xprt_close()` and
  `svc_clean_up_xprts()` reach `svc_delete_xprt()` without calling
  `xpo_kill_temp_xprt`.
- `XPT_CHNGBUF`: does not make a transport ready; it waits for the next
  `svc_udp_recvfrom()`, which test-and-clears it. `svc_sock_update_bufs()`
  sets it on every transport on `sv_permsocks`, and no other receive method
  consumes it.
- `XPT_RPCB_UNREG`: set by `svc_udp_init()` and, for a listener, by
  `svc_tcp_init()`; `svc_delete_xprt()` tests it and unregisters from
  rpcbind. That code casts the transport to `struct svc_sock`, so only a
  socket transport may set the bit.
- `XPT_PEER_VALID`: set once, on an `XPT_TEMP` transport only, by
  `svc_xprt_set_valid()`, which also decrements `sv_tmpcnt`;
  `svc_check_conn_limits()` closes only transports without it.
