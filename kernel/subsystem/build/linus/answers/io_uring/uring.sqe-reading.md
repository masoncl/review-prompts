- SQE pointer lifetime: `io_commit_sqring()` publishes the SQ head at the end
  of `io_submit_sqes()`, so the slot stays unreused through prep and through an
  issue that carries `IO_URING_F_INLINE`, and no longer.
- `sqe_copy` in `struct io_cold_def`: only `IORING_OP_URING_CMD` and
  `IORING_OP_URING_CMD128` have one; no other opcode's SQE is copied.
- `io_uring_cmd_prep()`: stores the ring pointer in `ioucmd->sqe`;
  `io_uring_cmd_sqe_copy()` later copies into `sqes` of `struct io_async_cmd`
  and re-points it.
- Inline issue that returns `-EIOCBQUEUED`: no copy is made; `ioucmd->sqe`
  still points into the ring after `io_submit_sqes()` returns.
- **Potentially unsafe usage**: a prep or issue handler reading an SQE field
  with a plain load.
  - Unsafe: when the SQE is in the ring and the value is stored or used after
    the load; `io_get_sqe()` returns a pointer into `ctx->sq_sqes`, which
    userspace can rewrite between the check and the use.
  - Safe: when the load only rejects a field and the value is never used
    again, as `io_fsync_prep()` does with `sqe->addr` and
    `__io_timeout_prep()` with `sqe->len`.
  - Safe: when the SQE is a kernel copy, as in `io_uring_sync_msg_ring()`;
    `io_uring_register_send_msg_ring()` fills it with `copy_from_user()`.
- **Potentially unsafe usage**: keeping the `sqe` pointer in the request.
  - Unsafe: when the opcode has no `sqe_copy` handler, or the pointer is read
    after an inline issue returned `-EIOCBQUEUED`.
  - Safe: read during an issue that no inline `-EIOCBQUEUED` preceded, with an
    `sqe_copy` handler installed, as `blkdev_uring_cmd()` does on its first
    issue; `io_req_sqe_copy()` returns `-EFAULT` if a copy is needed without
    `IO_URING_F_INLINE`.
- Request fields: zero only in a fresh slab object (`__GFP_ZERO` in
  `__io_alloc_req_refill()`); `io_req_add_to_cache()` recycles without
  clearing.
- `io_init_fail_req()`: zeroes `req->cmd.data` when `io_init_req()` fails
  before prep, because `io_req_defer_failed()` still calls the `fail` handler,
  for example `io_sendrecv_fail()` reading `done_io`.
- `io_req_add_to_cache()`: calls `io_poison_cached_req()` under `CONFIG_KASAN`
  only; it poisons `ctx`, `tctx`, `file`, `creds`, `apoll` and the task-work
  function, not the rest of `cmd`.
- There is no io_rw_prep() or io_prep_rw_setup() here; see `io_prep_rw()` and
  `__io_prep_rw()` in `io_uring/rw.c`.
- Prep setting what it later reads: `io_sendmsg_prep()` (`done_io`),
  `io_connect_prep()` (`in_progress`), `__io_splice_prep()` (`rsrc_node`).
