- Completions that return entries: `svc_rdma_wc_send()` returns
  `sc_sqecount`, `svc_rdma_wc_read_done()` returns `cc_sqecount`.
- `svc_rdma_write_done()` and `svc_rdma_reply_done()` in
  `net/sunrpc/xprtrdma/svc_rdma_rw.c`: return no entries; on error they
  trace and call `svc_rdma_xprt_deferred_close()`.
- Write and Reply chunk entries: `svc_rdma_cc_link_wrs()` adds `cc_sqecount`
  to `sc_sqecount`, so `svc_rdma_wc_send()` returns them.
- Chained chunk WRs: `rdma_rw_ctx_wrs()` installs its `cqe` only when
  `chain_wr` is NULL, and `svc_rdma_cc_link_wrs()` always passes the existing
  chain.
- There is no svc_rdma_wc_write() or svc_rdma_wc_reply_done() in this tree.
- `svc_rdma_sq_wait()` in `net/sunrpc/xprtrdma/svc_rdma_sendto.c`: the only
  place that reserves entries; `svc_rdma_post_send()` and
  `svc_rdma_post_chunk_ctxt()` both call it before `ib_post_send()`.
- Order: ticket order. A caller that fails the fast path takes a ticket from
  `sc_sq_ticket_head` and sleeps on `sc_sq_ticket_wait` until
  `sc_sq_ticket_tail` equals its ticket.
- Head of the line: only the thread whose ticket is being served sleeps on
  `sc_send_wait`.
- Both `wait_event()` calls are non-exclusive; the order comes from the
  tickets, not from the waitqueue.
- Fast path: tried first with no ticket, so a new caller takes entries ahead
  of ticket holders when enough are free.
- `XPT_CLOSE`: tested only on the slow path, in and after each
  `wait_event()`; the fast path returns 0 on a closing transport.
- Every ticket holder, on success and at `out_close`: increments
  `sc_sq_ticket_tail` exactly once, then `wake_up()` on `sc_sq_ticket_wait`.
- At `out_close` no entries are held: each failed `atomic_sub_return()` is
  undone at once by `atomic_add()`, so there is nothing to return.
- **Unsafe usage**: a slow-path exit from `svc_rdma_sq_wait()` that skips the
  increment of `sc_sq_ticket_tail`.
  - Unsafe: every later ticket holder sleeps on `sc_sq_ticket_wait` until the
    transport closes.
  - Safe: both slow-path exits of `svc_rdma_sq_wait()` increment and wake.
- `svc_rdma_wake_send_waiters()`: wakes `sc_send_wait` only, never
  `sc_sq_ticket_wait`.
- `svc_rdma_xprt_deferred_close()` in
  `net/sunrpc/xprtrdma/svc_rdma_transport.c`: calls
  `svc_xprt_deferred_close()`, then `wake_up_all()` on `sc_sq_ticket_wait`
  and on `sc_send_wait`.
- Server RDMA code calls `svc_xprt_deferred_close()` nowhere else; every
  completion handler and the forward paths use the wrapper.
- **Unsafe usage**: calling `svc_xprt_deferred_close()` on `rdma->sc_xprt`
  from a completion handler.
  - Unsafe: it sets `XPT_CLOSE` and enqueues but wakes neither waitqueue, so
    the close itself does not wake sleepers in `svc_rdma_sq_wait()`.
  - Safe: `svc_rdma_xprt_deferred_close()`, as `svc_rdma_wc_send()` and
    `svc_rdma_wc_read_done()` do.
- `svc_xprt_close()` path: does not go through the wrapper;
  `svc_rdma_detach()` does the two `wake_up_all()` calls itself.
