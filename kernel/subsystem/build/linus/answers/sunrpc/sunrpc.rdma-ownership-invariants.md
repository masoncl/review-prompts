- The rules are written down: a comment block titled "Reply-side ownership
  invariants" sits directly above the kerneldoc of
  `rpcrdma_reply_handler()` in `net/sunrpc/xprtrdma/rpc_rdma.c`. It has
  rules I1 to I5 and a "Non-hazards" list.

| Rule | Says | Assertion in code |
|---|---|---|
| I1 | a rep belongs to the HCA from `ib_post_recv()` to its Receive completion, then to the CPU until `rpcrdma_rep_put()` | `WARN_ON_ONCE(rep->rr_rqst)` in `rpcrdma_post_recvs()` |
| I2 | a rep reachable through `rl_reply` is not re-posted; `rpcrdma_reply_put()` clears `rl_reply` before `rpcrdma_rep_put()` | none |
| I3 | on entry to `rpcrdma_complete_rqst()` every MR of the req is invalidated and DMA-unmapped | `WARN_ON_ONCE()` in `rpcrdma_complete_rqst()` if `rl_registered` is not empty |
| I4 | `rl_kref` holds an RPC-layer and a Send-side reference; the req is pooled only after both drop | `WARN_ON_ONCE(req->rl_sendctx)` in `rpcrdma_req_release()` |
| I5 | the RPC layer owns a req from slot acquisition to `xprt_rdma_free_slot()` or `xprt_rdma_bc_free_rqst()`; pools hold no req with work outstanding | none |

- I2 in the comment: claims `rpcrdma_reply_put()` WARNs; the function in
  `net/sunrpc/xprtrdma/verbs.c` has no WARN.
- I4 in the comment: names xprt_rdma_bc_rqst_get, which does not exist; the
  function is `rpcrdma_bc_rqst_get()` in
  `net/sunrpc/xprtrdma/backchannel.c`.
- `rpcrdma_rep_put()`: clears `rr_rqst` itself, which is what the I1
  assertion relies on.
- I4 consequence: an RPC may complete while its Send is still outstanding.
  Only the return of the req to its pool waits for
  `rpcrdma_sendctx_unmap()`.
- `xprt_rdma_free()`: does not touch `rl_kref`.
