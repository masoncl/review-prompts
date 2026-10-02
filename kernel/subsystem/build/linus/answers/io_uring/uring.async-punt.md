- `io_queue_async()` order: fail unless the return is `-EAGAIN` and
  `REQ_F_NOWAIT` is clear; `io_req_sqe_copy()`; `io_arm_poll_handler()`; act
  on its result.
- `io_req_sqe_copy()` runs before `io_arm_poll_handler()`, so it covers all
  three results, not only the io-wq one.
- `IO_APOLL_READY`: `io_req_task_queue()`, so the retry runs from task work,
  not in `io_queue_async()`.
- Linked timeout: `__io_issue_sqe()` calls `__io_prep_linked_timeout()` before
  the handler and `io_queue_linked_timeout()` after it, whatever the handler
  returned; `io_queue_async()` does not touch the timeout.
- `io_arm_poll_handler()` and `io_arm_apoll()` return `IO_APOLL_ABORTED` when:
  - the opcode has neither `pollin` nor `pollout` (`io_arm_poll_handler()`
    only)
  - `io_file_can_poll()` is false
  - `io_req_alloc_apoll()` returns NULL: allocation failed, or the
    `APOLL_MAX_RETRY` budget of this request is used up
  - `__io_arm_poll_handler()` returns negative: `vfs_poll()` queued no wait
    entry or set an error, and reported no event
- `REQ_F_POLLED`: does not refuse poll; it means `req->apoll` exists and is
  reused.
- `REQ_F_NOWAIT` and `IORING_SETUP_IOPOLL`: not tested in
  `io_arm_poll_handler()`; `REQ_F_NOWAIT` is tested earlier in
  `io_queue_async()`.
- `io_queue_iowq()`: fails the request with `-ECANCELED` through
  `io_req_task_queue_fail()` when `current` is `PF_KTHREAD` or the task has no
  `tctx->io_wq`.
- `io_prep_async_work()`: `unbound_nonreg_file` does not apply to block
  devices; they stay on bounded workers.
- `io_prep_async_work()`: hashing applies to regular files with
  `hash_reg_file`, except `O_DIRECT` files with `FOP_DIO_PARALLEL_WRITE`, and
  to any regular file request with `REQ_F_IOPOLL`.
- io-wq poll attempt after `-EAGAIN`: `IO_APOLL_READY` and `IO_APOLL_ABORTED`
  both lead to a blocking retry in the worker.
