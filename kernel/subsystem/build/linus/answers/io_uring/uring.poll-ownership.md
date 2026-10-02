- `io_poll_get_ownership()` slow-path test: compares the whole `poll_refs`
  value, cast to unsigned and not masked, with `IO_POLL_REF_BIAS`; while
  `IO_POLL_CANCEL_FLAG` or `IO_POLL_RETRY_FLAG` is set, every attempt takes
  `io_poll_get_ownership_slowpath()`.
- `io_poll_get_ownership_slowpath()`: ORs in `IO_POLL_RETRY_FLAG`; it
  increments, and can win ownership, only if the reference bits were zero.
  It does not set the count to `IO_POLL_REF_BIAS`.
- `__io_arm_poll_handler()`: starts `poll_refs` at 1 only with
  `IO_URING_F_UNLOCKED`; without it it starts at 0 and the arming code is not
  the owner.
- Arming without ownership: must call `io_poll_can_finish_inline()` before it
  completes inline or calls `__io_poll_execute()`; when that fails it calls
  `io_poll_mark_cancelled()` (arming error) or leaves the request hashed, and
  returns 0.
- `io_poll_check_events()`: releases ownership only at the loop exit that
  returns `IOU_POLL_NO_ACTION`; every other return keeps the references, so
  no later wakeup can queue task_work.
- `IOU_POLL_REQUEUE`: `io_poll_task_func()` requeues with
  `__io_poll_execute()`, not `io_poll_execute()`, because it still owns the
  request.
- There is no io_poll_remove_one() here; cancel is `io_poll_cancel_req()`
  (mark, then `io_poll_execute()`), and `IORING_OP_POLL_REMOVE` uses
  `io_poll_disarm()`, which returns `-EALREADY` without ownership.
- **Potentially unsafe usage**: writing `req->flags` or unlinking a wait
  entry without ownership.
  - Unsafe: from a wakeup after `io_poll_get_ownership()` returned false,
    when it writes `req->flags`, or touches the request after `poll->head` is
    stored NULL; `io_poll_task_func()` may be completing the request at the
    same time.
  - Safe: `io_pollfree_wake()` on `POLLFREE`: marks cancelled, calls
    `io_poll_execute()`, then only unlinks with `io_poll_remove_waitq()`,
    whose `smp_store_release()` of `poll->head` must come last because
    `io_poll_remove_entry()` skips the waitqueue lock once it reads NULL.
  - Safe: `io_poll_double_prepare()` sets `REQ_F_DOUBLE_POLL` under the first
    entry's `head->lock`, which `io_poll_wake()` runs under
    (`__wake_up_common()` asserts it).
  - Safe: `__io_queue_proc()` sets `REQ_F_SINGLE_POLL` before the first
    `add_wait_queue()`, when no entry can fire.
