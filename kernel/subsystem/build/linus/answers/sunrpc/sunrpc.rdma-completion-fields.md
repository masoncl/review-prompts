- When `status` is not `IB_WC_SUCCESS`: handlers under
  `net/sunrpc/xprtrdma/` read only `wr_cqe` and `status`, and get the
  transport from `cq->cq_context`, not from `wc->qp`.
- `vendor_err`: read only by the tracepoint classes in
  `include/trace/events/rpcrdma.h`, never by handler logic.
- Client handlers: never test `IB_WC_WR_FLUSH_ERR` and never log. A flush
  and any other error take the same path through
  `rpcrdma_flush_disconnect()`.
- `svc_rdma_wc_receive()` with `IB_WC_SUCCESS`: still drops the Receive and
  closes the transport when `svc_rdma_refresh_recvs()` fails.
- `svc_rdma_wc_receive()`: copies `wc->byte_len` only after that repost
  step, not straight after the status test.
