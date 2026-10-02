- `struct rpcrdma_xprt`: has no counter of its own; it lives and dies with
  the `kref` of the embedded `struct rpc_xprt` (`rx_xprt`).
- `rl_kref` in `struct rpcrdma_req`: counts owners that keep the req out of
  its free pool. It does not arbitrate Send against Reply, and matching a
  Reply in `rpcrdma_reply_handler()` neither takes nor drops a reference.
- `rl_kref` RPC-layer reference: `kref_init()` in `xprt_rdma_alloc_slot()`,
  `rpcrdma_bc_rqst_get()` and `rpcrdma_req_release()`; dropped in
  `xprt_rdma_free_slot()` or `xprt_rdma_bc_free_rqst()`.
- `rl_kref` Send-side reference: `kref_get()` at the end of
  `rpcrdma_prepare_send_sges()` for every prepared Send, whatever
  `sc_unmap_count` is; dropped in `rpcrdma_sendctx_unmap()`.
- `rpcrdma_req_release()` in `net/sunrpc/xprtrdma/transport.c`: the only
  release function; there is no rpcrdma_reply_done() or
  rpcrdma_sendctx_done() here. It re-initialises the kref and hands the req
  to `bc_pa_list`, a backlog waiter, or `rb_send_bufs`.
- Unsignaled Send: its sendctx, and so its req reference, stays held until
  a later Send completion walks the ring (`rpcrdma_sendctx_put_locked()`)
  or until disconnect (`rpcrdma_sendctxs_destroy()`).
  `rpcrdma_buffer_create()` allocates `rpcrdma_req_pool_slack()` extra reqs
  to cover that delay.
- `struct rpcrdma_rep`: survives a reconnect. Created only on demand by
  `rpcrdma_rep_create()` from `rpcrdma_post_recvs()`; freed only by
  `rpcrdma_reps_destroy()` from `rpcrdma_buffer_destroy()`. Disconnect only
  DMA-unmaps it (`rpcrdma_reps_unmap()`). There is no rr_temp field.
- `rpcrdma_rep_resize()`: reallocates a surviving rep's buffer when the new
  connection's `re_inline_recv` is larger.
- `struct rpcrdma_mr`: belongs to one connection. Every MR is destroyed at
  disconnect: those on `rl_registered` by `rpcrdma_req_reset()`, the rest by
  `rpcrdma_mrs_destroy()`.
- `rpcrdma_req_reset()`: frees `rl_rdmabuf` and calls `frwr_mr_release()` on
  MRs still registered; it does not call `frwr_reset()`.
- `ep->re_write_pad_mr`: one MR taken at connect by `frwr_wp_create()`, with
  `mr_req` NULL and on no req list; `rpcrdma_xprt_connect()` fails if it
  cannot be made. `frwr_mr_put()` dereferences `mr_req`, so this MR must
  never reach it.
- `rl_rdmabuf`: the one regbuf that is per connection; allocated and mapped
  by `rpcrdma_req_setup()`, freed at disconnect. `rl_sendbuf` and
  `rr_rdmabuf` survive and are remapped on next use.
- `struct rpcrdma_sendctx` ring: per connection; `rpcrdma_sendctxs_create()`
  allocates it and `rpcrdma_sendctxs_destroy()` frees it.
- Per-connection setup in `rpcrdma_xprt_connect()`: sendctxs, `rl_rdmabuf`,
  MRs and the write-pad MR are built only after the connection is
  established; the first Receives are posted before `rdma_connect()`.
- `rpcrdma_xprt_disconnect()`: also runs from `xprt_rdma_connect_worker()`
  when `rpcrdma_xprt_connect()` fails, so each teardown step must tolerate
  objects that were never set up.
