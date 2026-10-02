- `fuse_uring_cancel()` on `FRRS_AVAILABLE`: unlinks the entry and clears
  `ent->cmd` under `queue->lock`, then completes the command with `-ENOTCONN`.
- `fuse_uring_cancel()` then frees the entry and drops `ring->queue_refs`,
  waking `stop_waitq` at 0; in any other state it does nothing.
- `ring->queue_refs`: incremented per entry in `fuse_uring_create_ring_ent()`.
- `ring->queue_refs` is decremented in `fuse_uring_stop_list_entries()`,
  `fuse_uring_cancel()`, the cancel branch of `fuse_uring_send_in_task()` and
  the abort branch of `fuse_uring_do_register()`.
- `fuse_uring_teardown_entries()`: takes entries from `ent_in_userspace` and
  `ent_avail_queue` only.
- Count above 0 after a pass: the entries left are in another state, for
  example on `ent_w_req_queue` or `ent_commit_queue`, or off-list after a
  failed copy; a later pass picks them up.
- `fuse_uring_stop_queues()`: does not wait for `ring->queue_refs`; with
  entries left it takes `fuse_conn_get()` and schedules
  `async_teardown_work`.
- `fuse_uring_async_stop_queues()`: at count 0 wakes `stop_waitq` and calls
  `fuse_conn_put()`.
- `fuse_uring_wait_stopped_queues()`: the sleeper; called from
  `fuse_chan_wait_aborted()`, which `fuse_conn_destroy()` calls.
- `fuse_uring_destruct()` also frees `queue->bufpool`.
- **Potentially unsafe usage**: `kfree()` of a ring entry outside
  `fuse_uring_destruct()`.
  - Unsafe: where a command whose pdu points at the entry can still be on the
    cancelable list, as in teardown; `fuse_uring_cancel()` reads `ent->queue`
    before it takes any lock.
  - Safe: in `fuse_uring_cancel()`, after `io_uring_cmd_done()` took the
    command off that list; the cancel runs under `ctx->uring_lock`
    (`io_uring_try_cancel_uring_cmd()` asserts it).
  - Safe: in the cancel branch of `fuse_uring_send_in_task()`, after
    `io_uring_cmd_done()`; task work runs under `ctx->uring_lock`.
  - Safe: in `fuse_uring_do_register()` when `fch->connected` is 0, before
    `fuse_uring_prepare_cancel()` has set the pdu.
  - Safe: park the entry on `ent_released` with `FRRS_RELEASED`, as
    `fuse_uring_entry_teardown()` does.
- **Unsafe usage**: calling `io_uring_cmd_mark_cancelable()` on a command
  whose pdu does not hold the entry.
  - Safe: `fuse_uring_prepare_cancel()` stores the entry in the pdu and then
    marks the command, as `fuse_uring_do_register()` and
    `fuse_uring_commit_fetch()` use it for each new command;
    `uring_cmd_to_ring_ent()` in the cancel trusts the pdu.
- **Unsafe usage**: freeing an entry outside destruct without dropping
  `ring->queue_refs`.
  - Safe: `atomic_dec_and_test()` and wake `stop_waitq`, as
    `fuse_uring_cancel()` does; `fuse_uring_wait_stopped_queues()` waits for 0.
