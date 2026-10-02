- Allocation: `io_alloc_ocqe()` adds `__GFP_ACCOUNT`; `io_cqe_overflow()`
  passes `GFP_KERNEL` before taking `completion_lock`;
  `io_cqe_overflow_locked()` passes `GFP_NOWAIT`. Neither uses `GFP_ATOMIC`.
- `io_cqe_overflow()`: used on `IO_RING_F_LOCKLESS_CQ` rings by
  `__io_submit_flush_completions()` and by `io_add_aux_cqe()`; it can sleep.
- CQEs that can be dropped: any that reach `io_cqring_add_overflow()` with a
  NULL entry, which is final CQEs, `io_post_aux_cqe()` and `io_add_aux_cqe()`.
- `io_req_post_cqe()`, `io_req_post_cqe32()` and
  `io_defer_get_uncommited_cqe()`: for the CQE they post, never queue an
  overflow entry and never touch `rings->cq_overflow` or
  `IO_CHECK_CQ_DROPPED_BIT`; they return false.
- `__io_cqring_overflow_flush()` with `dying` true: frees entries without
  posting and without counting them in `rings->cq_overflow`.
- `-EBADR`: returned by `io_cqring_wait()` in `io_uring/wait.c` and by
  `io_iopoll_check()`.
- `io_uring_enter`: returns `-EBADR` and clears `IO_CHECK_CQ_DROPPED_BIT`
  only when the submit part of the same call returned 0; otherwise the
  submit count is returned and the bit stays set.
- There is no cq_extra field and no IORING_SETUP_CQ_NODROP in this tree;
  `IORING_FEAT_NODROP` is the feature bit.
