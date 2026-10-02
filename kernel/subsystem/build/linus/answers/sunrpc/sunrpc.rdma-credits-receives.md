- Order in `rpcrdma_reply_handler()`:
  1. decode the four header words;
  2. sanitise the grant, before the version check and before
     `rpcrdma_is_bcall()`;
  3. look up and pin the rqst;
  4. `rpcrdma_update_cwnd()`, if the grant changed;
  5. attach the rep, then `frwr_unmap_async()` or `rpcrdma_complete_rqst()`;
  6. `rpcrdma_post_recvs()`, last, at `out_post`.
- Receives are therefore posted after the congestion window has been
  updated and after the RPC was completed or its LOCAL_INV chain posted.
- Upper clamp of the grant: `r_xprt->rx_ep->re_max_requests`.
- Count passed: `credits + (buf->rb_bc_srv_max_requests << 1)`.
- `rpcrdma_post_recvs()`: takes two arguments, `r_xprt` and `needed`; there
  is no `temp` argument.
- Count posted: nothing while `re_receive_count > needed`; otherwise up to
  `needed - re_receive_count + ep->re_recv_batch`.
  `re_recv_batch` is `re_max_requests >> 2`, set in `frwr_query_device()`.
  The client does not use `RPCRDMA_MAX_RECV_BATCH`; only the server does.
- `out_norqst`: posts with the sanitised wire grant but does not update the
  congestion window.
- `out_badversion` and `out_shortreply`: post with the stored
  `buf->rb_credits`, not the value from the wire.
- Backchannel call: when `rpcrdma_is_bcall()` returns true the handler
  returns without calling `rpcrdma_post_recvs()` or
  `rpcrdma_update_cwnd()`.
