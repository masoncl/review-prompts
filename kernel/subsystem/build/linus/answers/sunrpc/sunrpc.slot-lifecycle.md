- `XPRT_CONGESTED` already set: `xprt_reserve()` sleeps the task on
  `xprt->backlog` without trying to allocate; `xprt_retry_reserve()` skips
  that test.
- `tk_status` `-EAGAIN` from `xprt_alloc_slot()`: the task sleeps on
  `xprt->backlog`.
- `tk_status` `-ENOMEM` from `xprt_alloc_slot()`: no backlog sleep;
  `call_reserveresult()` does `rpc_delay()` and goes to
  `call_retry_reserve()`.
- There is no xprt_lock_and_alloc_slot() here; `xs_udp_ops`, `xs_tcp_ops`,
  `xs_local_ops` and `bc_tcp_ops` all use `xprt_alloc_slot()`.
- RPC/RDMA: `xprt_rdma_alloc_slot()` takes slots from `rpcrdma_buffer_get()`
  and re-checks the pool after joining the backlog.
- `xprt_rdma_free_slot()`: drops a kref; the slot reaches a waiter or the pool
  only in `rpcrdma_req_release()`, after the Send side has dropped its
  reference too.
- `xprt_free_slot()`: hands the slot to the first backlog waiter through
  `xprt_wake_up_backlog()`; the waiter's callback
  `xprt_complete_request_init()` runs `xprt_request_init()`.
- `call_reserveresult()`: never calls `xprt_release()`; status 0 with no slot
  becomes `-EIO`.
- Other callers of `xprt_release()`: search for them; the surprising ones are
  `call_decode()` on `-EKEYREJECTED`, to force a new XID, and
  `rpc_task_set_transport()` when moving a task off an `XPRT_OFFLINE`
  transport.
- `xprt_release()` with no slot: calls `xprt_release_write()` only if
  `task->tk_client` is set.
- `xprt_release()` with a slot, in order:
  1. `xprt_request_dequeue_xprt()`, which waits for pins.
  2. Under `transport_lock`: `release_xprt`, `release_request` if set,
     `xprt_schedule_autodisconnect()`.
  3. `buf_free` if `rq_buffer` is set.
  4. `put_rpccred()` on `rq_cred`.
  5. `rq_release_snd_buf` if set.
  6. Clears `tk_rqstp`, then `free_slot`, or `xprt_free_bc_request()` for a
     preallocated backchannel request.
- There is no xprt_request_dequeue_all() here; `xprt_request_dequeue_xprt()`
  does that job.
- `xprt_release()` does not call `xdr_free_bvec()` itself. The send bvec is
  freed in `xprt_request_dequeue_transmit_locked()`, the receive bvec in
  `xprt_complete_rqst()` or `xprt_request_dequeue_xprt()`.
