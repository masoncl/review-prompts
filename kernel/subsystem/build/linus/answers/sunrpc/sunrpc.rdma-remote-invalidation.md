- `frwr_reminv()`: has no MR state to set. It unlinks the matching MR and
  calls `frwr_mr_put()`; FRWR_IS_INVALID and FRWR_FLUSHED_LI do not exist in
  this tree.
- No match for `rr_inv_rkey` in `frwr_reminv()`: the list is left unchanged
  and every MR goes through `frwr_unmap_async()`.
- Failed or flushed LOCAL_INV: there is no rpcrdma_mr_recycle() here.
  `frwr_mr_done()` and `frwr_wc_localinv_done()` simply skip
  `frwr_mr_put()`, so the MR is on no req list and stays DMA-mapped.
- Destruction of such an MR: `rpcrdma_mrs_destroy()` finds it on
  `rb_all_mrs` at disconnect and calls `frwr_mr_release()`.
- MRs still on `rl_registered` at disconnect: destroyed earlier, by
  `rpcrdma_req_reset()`, which unlinks them from `rb_all_mrs` first.
- `mrs_recycled` and `mrs_orphaned` in `struct rpcrdma_stats`: printed by
  `xprt_rdma_print_stats()` but never incremented.
