- There is no svc_rqst_alloc() here; `svc_prepare_thread()` in
  `net/sunrpc/svc.c` allocates the `struct svc_rqst` and links it to the pool.
- `XPT_BUSY` is not held for the length of a request: `svc_xprt_received()`
  clears it, and the receive method calls that before it returns, for example
  `svc_tcp_recvfrom()` and `svc_rdma_recvfrom()`.
- `svc_xprt_release()` does not clear `XPT_BUSY`; another thread can be
  receiving on the same transport while this request is processed.
- `struct svc_serv` has no sv_nrpools field; use `svc_serv_nrpools()`, which
  returns `svc_pool_map.npools` when `sv_is_pooled` is set and 1 otherwise.
- `struct svc_rqst` has no rq_xprt_hlen field.
- `struct svc_pool` has no sp_sockets list; `sp_xprts` is a `struct lwq`
  linked through `xpt_ready`.
- There is no xpo_reserve_space method; the reply reservation is
  `rq_reserved`, added to `xpt_reserved` in `svc_handle_xprt()` after the
  receive method returns.
- `rq_server` and `xpt_server` are uncounted pointers: `struct svc_serv` has
  no reference count, and `svc_destroy()` frees it after only a `WARN_ONCE()`
  if `sv_permsocks` or `sv_tempsocks` is not empty.
