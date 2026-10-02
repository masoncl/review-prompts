| Helper | Context and locks | Overflow | Flush |
|---|---|---|---|
| `io_post_aux_cqe()` | process context; takes `completion_lock` on every ring; caller meets the rest of "CQ locking" | yes, `GFP_NOWAIT`; false if dropped | itself |
| `io_add_aux_cqe()` | `uring_lock` held; asserts `IO_RING_F_LOCKLESS_CQ` | yes, `GFP_KERNEL`; returns void | later, via `cq_flush` |
| `io_req_post_cqe()` | `uring_lock` held; asserts not an io-wq worker | no; returns false | later, via `cq_flush` |
| `io_req_post_cqe32()` | as `io_req_post_cqe()` | no; returns false | later, via `cq_flush` |
| `io_defer_get_uncommited_cqe()` | caller meets "CQ locking"; takes no lock | no; returns false | later, via `cq_flush` |

- `io_post_aux_cqe()` on an `IORING_SETUP_IOPOLL` or
  `IORING_SETUP_DEFER_TASKRUN` ring: the caller holds `uring_lock` itself;
  `__io_msg_ring_data()` takes it for `IORING_SETUP_IOPOLL` targets.
- `io_post_aux_cqe()` lock: plain `spin_lock()`, and `io_get_cqe_overflow()`
  asserts `in_task()`.
- `io_add_aux_cqe()`: does not take or need `completion_lock` to fill;
  `io_cqe_overflow()` takes it only to queue an overflow entry.
- `submit_state.cq_flush`: makes `io_submit_flush_completions()` commit the
  tail even with empty `compl_reqs`; the caller's path must reach it before
  dropping `uring_lock`.
- `io_req_post_cqe32()`: `io_fill_cqe_aux32()` does `WARN_ON_ONCE()` and
  returns false on a ring with neither `IORING_SETUP_CQE32` nor
  `IORING_SETUP_CQE_MIXED`; it overwrites `cqe[0].user_data` in the caller's
  array.
- `io_defer_get_uncommited_cqe()`: defined in `io_uring/io_uring.h`; the
  caller writes the slot, as `io_zcrx_queue_cqe()` does.
