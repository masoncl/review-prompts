- `frwr_map()`: takes `struct rpcrdma_xdr_cursor *cur` in place of a segment
  array and count, and returns `int`: 0, or `-EIO`.
- There is no struct rpcrdma_mr_seg, rl_segments or rpcrdma_convert_iovs()
  in this tree; `frwr_map()` builds `mr->mr_sg` straight from `cur->xc_buf`.
- `struct rpcrdma_xdr_cursor` in `net/sunrpc/xprtrdma/xprt_rdma.h`: holds
  the `xdr_buf`, `xc_page_offset`, and the flags `XC_HEAD_DONE`,
  `XC_PAGES_DONE`, `XC_TAIL_DONE`. A set flag means "nothing left to
  register", whether already registered or excluded.
- `rpcrdma_xdr_cursor_init()`: selects the regions by presetting flags. A
  non-zero `pos` excludes the head; `rpcrdma_readch` and `rpcrdma_writech`
  exclude the tail.
- Caller loop in the three encoders: `do { rpcrdma_mr_prepare(); encode one
  segment; } while (!rpcrdma_xdr_cursor_done(&cur))`. The loop ends on the
  cursor; no segment count is passed to or returned by `frwr_map()`.
- `rpcrdma_mr_prepare()`: returns `int` and hands the MR back through
  `struct rpcrdma_mr **mr`; `-EAGAIN` when no MR is free.
- One `frwr_map()` call: takes at most `re_max_fr_depth` entries. Without
  `IB_MR_TYPE_SG_GAPS` it stops gathering right after the head, and before
  a tail that would leave a gap; what it gathered is still registered.
- `frwr_map()` advances the cursor before it DMA-maps, so after `-EIO` the
  cursor is past data that was not registered. Callers abandon the cursor on
  error.
- Failed `ib_dma_map_sg()`: `frwr_map()` returns `-EIO` and leaves
  `mr->mr_device` NULL. `mr_dir` is never set to `DMA_NONE`.
- Failed `ib_map_mr_sg()`: `-EIO` with `mr->mr_device` already set, so the
  later unmap runs.
- Unwind: `rpcrdma_marshal_req()` calls `frwr_reset()`, which moves every MR
  on `rl_registered`, the failed one included, to `rl_free_mrs`. There is no
  rpcrdma_mr_put().
- **Unsafe usage**: setting `mr->mr_device` to a device before
  `ib_dma_map_sg()` has succeeded.
  - Unsafe: `frwr_mr_unmap()` treats a non-NULL `mr_device` as "mapped" and
    calls `ib_dma_unmap_sg()`.
  - Safe: assign `mr_device` only after a non-zero `ib_dma_map_sg()` return,
    as `frwr_map()` and `frwr_wp_create()` do.
