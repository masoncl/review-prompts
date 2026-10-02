- `xmit_queue`: a `struct list_head` linked through `rq_xmit`, not an rbtree.
- Order in `xprt_request_enqueue_transmit()`:
  - `rq_cong` set: inserted before the first request that holds no credit.
  - `rq_seqno_count == 0`: appended to the `rq_xmit2` list of the first queued
    request with the same `tk_owner`.
  - Otherwise, which includes every request with a GSS sequence number and no
    credit: tail of `xmit_queue`.
- `xprt_transmit()`: sends from the head, so it sends other tasks' requests,
  each one pinned; `-EBADMSG` from another task's request is treated as 0.
- Dequeuing the head of `xmit_queue`: `xprt_request_dequeue_transmit_locked()`
  calls `abort_send_request`; `xs_stream_abort_send_request()` forces a
  disconnect if part of the record was sent.
- A pin blocks only `xprt_request_dequeue_xprt()`, and so `xprt_release()` and
  re-encoding in `call_encode()`. It does not stop completion or a timeout
  wake-up.
- `xprt_wait_on_pinned_rqst()`: sleeps uninterruptibly, so a pin must always
  be dropped; RPC/RDMA holds one until `rpcrdma_complete_rqst()` or
  `rpcrdma_unpin_rqst()`.
- Copy target: the receiver writes `rq_private_buf`; `call_decode()` reads
  `rq_rcv_buf` only after it sees `rq_reply_bytes_recvd`.
- **Unsafe usage**: using the request from `xprt_lookup_rqst()` after dropping
  `queue_lock` without a pin.
  - Safe: `xprt_pin_rqst()` before unlocking, then `xprt_complete_rqst()` and
    `xprt_unpin_rqst()` under the lock again, as `xs_read_stream_reply()`
    does; `xprt_request_dequeue_xprt()` waits on `rq_pin`.
  - Safe: keep `queue_lock` held across the whole copy and completion with no
    pin, as `receive_cb_reply()` in `net/sunrpc/svcsock.c` does.
