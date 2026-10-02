- Models do not know `IOU_F_TWQ_IN_WAKE`. Wake handlers pass it, for example
  `io_futex_wake_fn()` and `io_waitid_wait()` to `__io_req_task_work_add()`
  and `io_poll_wake()` through `__io_poll_execute()`;
  `io_req_local_work_add()` then passes it to `io_eventfd_signal()` as
  `defer`, so the eventfd is signalled through `call_rcu_hurry()`, not inline.
- Models take `io_submit_sqes()` to always read `sq.tail`. With
  `IORING_SETUP_SQ_REWIND` it does not read it; it takes `ctx->sq_entries` as
  the number of entries available.
- Models take `ctx->flags` to be fixed after creation.
  `io_register_enable_rings()` clears `IORING_SETUP_R_DISABLED` with
  `smp_store_release()` after it sets `submitter_task` (on
  `IORING_SETUP_SINGLE_ISSUER` rings); `io_uring_enter()` pairs with
  `smp_load_acquire()`.
- Models take a registered-buffer send to import with the notification.
  That holds for zero-copy only; `IORING_OP_SEND` and `IORING_OP_RECV` accept
  `IORING_RECVSEND_FIXED_BUF`, and `io_send()` and `io_recv()` import with the
  request itself.
- Models take buffer cloning to need only the two ring locks.
  `io_register_clone_buffers()` returns `-EEXIST` if a different source ring
  has a `submitter_task` that is not `current`; `io_clone_buffers()` needs
  equal `user` and `mm_account`.
