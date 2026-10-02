- `frwr_unmap_async()`: called only from `rpcrdma_reply_handler()`, in
  Receive completion context.
- `frwr_unmap_sync()`: called only from `xprt_rdma_free()`, in process
  context; it never runs on the reply path and never completes an RPC.
- `frwr_wc_localinv_done()`: completes the RPC from the Send CQ's completion
  context, since `mr_cqe` belongs to a Send Queue WR.
- Empty `rl_registered` in the reply handler: `rpcrdma_complete_rqst()` is
  called directly. No `rl_kref` operation is involved in completing an RPC.
- `frwr_unmap_sync()` on return: guarantees only that `rl_registered` is
  empty. `frwr_wc_localinv_wake()` wakes the waiter whatever the status, and
  there is no wait at all when `bad_wr == first`.
- After a failed or unposted LOCAL_INV in `frwr_unmap_sync()`: the memory
  goes back to the caller with the MR still DMA-mapped; the forced
  disconnect is the recovery.
- **Potentially unsafe usage**: calling `frwr_reset()` to make a req's MRs
  reusable without invalidating them.
  - Unsafe: once `frwr_send()` has posted the req's `IB_WR_REG_MR` WRs; the
    rkeys may then be valid on the HCA.
  - Safe: after a failed marshal, as `rpcrdma_marshal_req()` does;
    `frwr_send()` is the only place that posts those WRs and it runs after
    marshalling.
