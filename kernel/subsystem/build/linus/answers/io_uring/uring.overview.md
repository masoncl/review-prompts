- Where the core lives: task_work is in `io_uring/tw.c` and `io_uring/tw.h`,
  `io_cqring_wait()` in `io_uring/wait.c`, `io_uring_try_cancel_requests()`
  and `io_uring_cancel_generic()` in `io_uring/cancel.c`; `io_uring/io_uring.c`
  keeps setup, submit, issue and CQ posting.
- `struct mpscq`: the type of both task_work queues; code under `io_uring/`
  does not call `llist_add()`.
- `struct io_tw_req`: what a task_work callback (`io_req_tw_func_t`) receives,
  by value, with an `io_tw_token_t`; the request is `tw_req.req`.
- `flags` in `struct io_ring_ctx`: holds only the `IORING_SETUP_*` flags;
  internal ring state is in `int_flags`.
- CQ locking is decided per ring. `io_uring_create()` sets
  `IO_RING_F_LOCKLESS_CQ` for `IORING_SETUP_DEFER_TASKRUN` or
  `IORING_SETUP_IOPOLL`; `IORING_SETUP_SINGLE_ISSUER` alone does not set it.
  - With `IO_RING_F_LOCKLESS_CQ`: `uring_lock` serialises the CQ.
  - Without it: `__io_submit_flush_completions()` takes `completion_lock`
    even though it holds `uring_lock`.
  - `cq_overflow_list`: under `completion_lock` on every ring;
    `io_cqring_add_overflow()` asserts it.
- Entry size is not fixed per ring:
  - `IORING_SETUP_CQE_MIXED`: a CQE with `IORING_CQE_F_32` takes two CQ slots;
    `io_fill_nop_cqe()` posts an `IORING_CQE_F_SKIP` filler when one would
    straddle the ring end.
- `struct io_kiocb` is not always built from an SQE. For example
  `io_msg_data_remote()` in `io_uring/msg_ring.c` allocates one from
  `req_cachep` only to carry a CQE to another ring by task_work.
  - Such a request takes its own `ctx->refs` reference, in
    `io_msg_remote_post()`.
- `struct io_rsrc_node`: unregistering does not wait for requests.
  `io_rsrc_data_free()` drops the table's reference on each slot and frees
  the table; the node lives until the last request puts it.
  - `refs` is a plain `int`; `io_put_rsrc_node()` asserts `uring_lock`.
- `struct io_mapped_ubuf`: has its own `refcount_t` `refs`, because
  `io_register_clone_buffers()` makes nodes in two rings point at one buffer.
- `struct io_br_sel`: the result of a provided-buffer selection.
  - `buf_list` in it is NULL after a selection made with
    `IO_URING_F_UNLOCKED`; the list can go away once `uring_lock` is dropped.
- `struct io_restriction` also hangs off the task, as `io_uring_restrict` in
  `struct task_struct`. It is set by `io_uring_register()` with fd -1.
  - `__io_uring_fork()` copies it to the child; `io_uring_create()` copies it
    into every ring the task creates (`io_ctx_restriction_clone()`).
- `struct io_bpf_filters`: per-opcode classic BPF filters inside a
  `struct io_restriction`; refcounted and shared copy-on-write between task
  and rings. `io_submit_sqe()` runs them after prep; a deny fails the request
  with `-EACCES`.
- `struct io_uring_bpf_ops` (`io_uring/bpf-ops.h`): a BPF struct_ops attached
  to one ring. While `loop_step` is set in the ctx, `io_uring_enter()` does
  nothing but `io_run_loop()`.
  - `struct iou_ctx`: an empty type; the `struct io_ring_ctx` pointer is cast
    to it for the BPF program.
- `struct io_zcrx_ifq` (`io_uring/zcrx.h`): one zero-copy receive queue. A
  ring holds it in the `zcrx_ctxs` xarray, but does not own it alone.
  - Another ring can import it (`ZCRX_REG_IMPORT`), so it has its own `refs`
    and `user_refs`.
  - `master_ctx`: the one ring that receives its notification CQEs.
  - Registering needs `IORING_SETUP_DEFER_TASKRUN` and one of
    `IORING_SETUP_CQE32` or `IORING_SETUP_CQE_MIXED`.
