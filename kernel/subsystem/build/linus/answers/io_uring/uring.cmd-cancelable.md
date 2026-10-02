- `io_uring_cmd_mark_cancelable()`: sets only `IORING_URING_CMD_CANCELABLE`
  in `cmd->flags`; it sets no `REQ_F_` flag.
- Lock: taken by `io_ring_submit_lock()` from `issue_flags`. A call with
  `IO_URING_F_UNLOCKED` (io-wq issue) is valid and takes `uring_lock` itself.
- No effect when `req->flags` has `REQ_F_IOPOLL`. `io_uring_cmd()` sets that
  only if the ring is `IORING_SETUP_IOPOLL` and the file has
  `->uring_cmd_iopoll`; on an IOPOLL ring with a file lacking it the mark
  takes effect.
- `REQ_F_IOPOLL` command: never gets an `IO_URING_F_CANCEL` call, so teardown
  cannot depend on one.
- `IORING_OP_ASYNC_CANCEL`: `io_try_cancel()` in `io_uring/cancel.c` does not
  visit `ctx->cancelable_uring_cmd`. The only sender of `IO_URING_F_CANCEL`
  is `io_uring_try_cancel_uring_cmd()`, from
  `io_uring_try_cancel_requests()`.
- Cancel call `issue_flags`: exactly `IO_URING_F_CANCEL |
  IO_URING_F_COMPLETE_DEFER`. `IO_URING_F_SQE128` and `IO_URING_F_CQE32` are
  absent, so `IO_URING_F_CANCEL` must be tested before those, as
  `fuse_uring_cmd()` does.
- Cancel call result: the return value is ignored and the handler may leave
  the command pending. `ublk_cancel_cmd()` skips a started request and
  `fuse_uring_cancel()` acts only in state `FRRS_AVAILABLE`.
- Repetition: `io_uring_try_cancel_uring_cmd()` returns true whenever it
  called a handler, and `io_uring_cancel_generic()` and `io_ring_exit_work()`
  loop on that with only `cond_resched()` between passes.
  `io_ring_exit_work()` calls the handler again until the command is
  completed.
- Sleeping: the handler runs in process context under the `uring_lock` mutex
  and may sleep; `ublk_start_cancel()` takes `ub->cancel_mutex` and quiesces
  the queue.
- pdu: state the handler reaches through the pdu must be written before the
  mark and stay valid until `io_uring_cmd_done()`; see `ublk_prep_cancel()`
  and `fuse_uring_prepare_cancel()`.
- **Unsafe usage**: returning a final value (neither `-EIOCBQUEUED` nor
  `-EAGAIN`) from the issue call after marking, without
  `io_uring_cmd_done()`. `io_uring_cmd()` completes the request without
  `io_uring_cmd_del_cancelable()`, leaving a freed request on
  `ctx->cancelable_uring_cmd`.
  - Safe: return `-EIOCBQUEUED` on every path after the mark, as
    `fuse_uring_cmd()` does once `fuse_uring_do_register()` has marked.
- **Unsafe usage**: marking a command that another context may already
  complete. `io_uring_cmd_del_cancelable()` tests the flag before taking the
  lock; a completion that runs first skips the unlink and the mark then links
  a finished request.
  - Safe: mark before the command is published to completers, as
    `fuse_uring_do_register()` does before it sets `ent->cmd`.
- **Unsafe usage**: in the `IO_URING_F_CANCEL` call, calling
  `io_uring_cmd_done()` with `IO_URING_F_UNLOCKED`, or on a marked command
  other than the one passed. The first relocks the held `uring_lock`; the
  second can unlink the entry that `hlist_for_each_entry_safe()` already
  saved as next.
  - Safe: complete only the passed command with the passed `issue_flags`, as
    `fuse_uring_cancel()` does.
