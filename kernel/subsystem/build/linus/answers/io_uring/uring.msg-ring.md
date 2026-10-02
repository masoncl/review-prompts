- Choice of path: `io_msg_need_remote()` tests only `IO_RING_F_TASK_COMPLETE`
  in the target's `int_flags`; no trylock result and no source flag is
  involved.
- Target with `IORING_SETUP_R_DISABLED`: `-EBADFD`, for both
  `IORING_MSG_DATA` and `IORING_MSG_SEND_FD`; nothing is queued.
- Target with `IORING_SETUP_DEFER_TASKRUN` and `IORING_SETUP_IOPOLL`:
  `IO_RING_F_TASK_COMPLETE` is not set, so the CQE is posted directly under
  the target's `uring_lock`.
- `IORING_MSG_SEND_FD` remote path: `io_msg_fd_remote()` uses
  `task_work_add()` with `TWA_SIGNAL` on the target's `submitter_task`, and
  returns `-EOWNERDEAD` if that fails. No private request is allocated.
  - `io_msg_tw_fd_complete()` then runs in the target task, posts with
    `io_post_aux_cqe()`, and completes the source request with
    `io_req_queue_tw_complete()`.
- `IORING_MSG_SEND_FD` direct path: `io_msg_install_complete()` always takes
  the target's `uring_lock`; `__io_msg_ring_data()` takes it only for
  `IORING_SETUP_IOPOLL` targets.
- There is no io_double_lock_ctx() here; `io_lock_external_ctx()` in
  `io_uring/msg_ring.c` does that.
- `IO_URING_F_UNLOCKED` callers of `io_lock_external_ctx()`: io-wq,
  `io_msg_tw_fd_complete()`, and `io_uring_sync_msg_ring()`, which has no
  source ring. All get the blocking `mutex_lock()`.
- `io_msg_remote_post()`: returns void, sets `req->tctx = NULL`, and has no
  test of `submitter_task`. The data path has no `-EOWNERDEAD`.
- `submitter_task` of the target: valid because the `smp_load_acquire()` test
  of `IORING_SETUP_R_DISABLED` pairs with the `smp_store_release()` in
  `io_register_enable_rings()`.
- Remote data path result: `io_msg_data_remote()` returns 0 once queued; an
  overflow or drop on the target is not reported to the sender.
- Private request and ring type: `io_req_task_work_add_remote()` does
  `WARN_ON_ONCE()` and returns on a ring without `IORING_SETUP_DEFER_TASKRUN`;
  `io_req_normal_work_add()` would dereference `req->tctx`.
- Freeing: `io_msg_tw_complete()` uses `kfree_rcu(req, rcu_head)`, then
  `percpu_ref_put()` on the target's `refs`.
- `kfree_rcu()` and the queueing code: `io_req_local_work_add()` does not
  touch the request after `mpscq_push()`; `zcrx_notif_tw()` in
  `io_uring/zcrx.c` frees the same kind of request with `kmem_cache_free()`.
- **Unsafe usage**: completing the private request through
  `io_req_task_complete()` or `io_req_complete_defer()`.
  `io_free_batch_list()` calls `io_put_task()`, which dereferences
  `req->tctx`, and puts the request in the target's cache.
  - Safe: a task work callback of its own that posts the CQE and frees the
    request, as `io_msg_tw_complete()` does.
