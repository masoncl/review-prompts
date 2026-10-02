- `svc_rdma_send_ctxt_put()` in `net/sunrpc/xprtrdma/svc_rdma_sendto.c`:
  releases nothing; it only adds the ctxt to `rdma->sc_send_release_list`.
- No workqueue is involved: there is no svcrdma_wq and no
  svc_rdma_send_ctxt_put_async() in this tree, and
  `struct svc_rdma_send_ctxt` has no work item.
- `svc_rdma_send_ctxt_release()`: the only place mappings and pages are
  released, other than SGE 0; its only caller is
  `svc_rdma_send_ctxts_drain()`, which takes the whole
  `sc_send_release_list` and runs in the calling thread.
- `svc_rdma_send_ctxt_release()` order: `svc_rdma_send_ctxt_unmap()` (chunk
  rw contexts, then `ib_dma_unmap_page()` on `sc_sges[1]` upward), then
  `release_pages()` on `sc_pages`, then `llist_add()` to `sc_send_ctxts`.
- SGE 0: unmapped only by `svc_rdma_send_ctxts_destroy()`, with
  `ib_dma_unmap_single()`.
- Drain triggers: search for callers of `svc_rdma_send_ctxts_drain()`. The
  usual one is `svc_rdma_release_ctxt()` (`xpo_release_ctxt`), which drains
  even when its context argument is NULL.
- Easy-to-miss drain callers: `svc_rdma_send_ctxt_get()` when the free list
  is empty, `svc_rdma_sq_wait()` after a slow-path success, and
  `svc_rdma_free()`.
- Self-trigger: when `svc_rdma_send_ctxt_put()` adds to an empty release
  list it sets `XPT_DATA` and calls `svc_xprt_enqueue()`, so an idle
  connection still gets a drain.
- Self-trigger refused: `svc_rdma_has_wspace()` returns 0 while
  `sc_send_wait` or `sc_sq_ticket_wait` has a sleeper, so `svc_xprt_ready()`
  rejects that enqueue; `svc_rdma_sq_wait()` drains for this reason.
- Error paths that never posted: use the same `svc_rdma_send_ctxt_put()`, so
  their release is deferred to a drain too.
- Teardown: `svc_rdma_free()` in `net/sunrpc/xprtrdma/svc_rdma_transport.c`
  calls `ib_drain_qp()`, then `svc_rdma_send_ctxts_drain()`, and only later
  `svc_rdma_send_ctxts_destroy()`, which walks `sc_send_ctxts` only.
- `svc_rdma_wc_send()` on any status other than `IB_WC_SUCCESS`, in order:
  1. `svc_rdma_wake_send_waiters()` with `ctxt->sc_sqecount`
  2. `trace_svcrdma_wc_send_flush()` for `IB_WC_WR_FLUSH_ERR`, otherwise
     `trace_svcrdma_wc_send_err()`
  3. `svc_rdma_send_ctxt_put()`
  4. `svc_rdma_xprt_deferred_close()`
- After step 3 the handler does not touch the ctxt; `rdma` comes from
  `cq->cq_context`.
