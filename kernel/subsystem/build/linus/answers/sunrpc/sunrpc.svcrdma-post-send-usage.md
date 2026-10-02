- A chain is one ctxt: `sc_wr_chain` heads the Write and Reply chunk WRs
  that `svc_rdma_cc_link_wrs()` linked ahead of `sc_send_wr`; `sc_send_wr`
  is last and its `next` stays NULL.
- Reuse after completion: once `svc_rdma_wc_send()` has queued the ctxt, any
  thread that calls `svc_rdma_send_ctxts_drain()` releases it, and
  `svc_rdma_send_ctxt_get()` then resets `sc_sqecount`, `sc_wr_chain`,
  `sc_page_count` and `num_sge`.
- `svc_rdma_post_send()` return values: only 0 or `-ENOTCONN`.

  | Return | Posted | SQ entries | Who puts the ctxt |
  |---|---|---|---|
  | 0 | whole chain | held until completion | `svc_rdma_wc_send()` |
  | 0 | part of the chain | not returned | not the caller |
  | `-ENOTCONN` | nothing | never taken, or returned | the caller |

- **Potentially unsafe usage**: reading or writing the ctxt after
  `ib_post_send()` was called on its chain.
  - Unsafe: when `svc_rdma_post_send()` returned 0; the ctxt may already be
    released and re-initialised for another Reply.
  - Safe: values copied before the post, as `svc_rdma_post_send()` does with
    `cid`, `sqecount` and `first_wr`; `trace_svcrdma_post_send()` runs before
    `ib_post_send()`.
  - Safe: after a negative return, because `svc_rdma_post_send_err()` returns
    `-ENOTCONN` only when `bad_wr == first_wr`.
- **Potentially unsafe usage**: calling `svc_rdma_send_ctxt_put()` after
  `svc_rdma_post_send()`.
  - Unsafe: when it returned 0, which includes a partial post; the ctxt is
    no longer the caller's.
  - Safe: when it returned a negative value, as `svc_rdma_sendto()`,
    `svc_rdma_send_error_msg()` and `rpcrdma_bc_send_request()` do.
- `svc_rdma_post_send_err()` in `net/sunrpc/xprtrdma/svc_rdma_sendto.c`:
  handles every `ib_post_send()` failure, for `svc_rdma_post_send()` and for
  `svc_rdma_post_chunk_ctxt()`.
- `svc_rdma_post_send_err()` always: traces, then calls
  `svc_rdma_xprt_deferred_close()`, not `svc_xprt_deferred_close()`.
- Partial post (`bad_wr != first_wr`): `svc_rdma_post_send_err()` returns 0,
  returns no SQ entries and puts nothing.
- Nothing posted (`bad_wr == first_wr`): `svc_rdma_post_send_err()` itself
  returns all `sqecount` entries through `svc_rdma_wake_send_waiters()` and
  returns `-ENOTCONN`.
- `svc_rdma_post_send_err()` never puts a ctxt and never returns entries for
  only part of a chain.
- `svc_rdma_wc_send()`: the only completion handler that puts a send ctxt or
  returns its `sc_sqecount`; see "Server Send Queue accounting" for the
  chunk handlers.
