- There is no io_ring_submitter_task() here; the tests are
  `io_allowed_run_tw()` and `io_allowed_defer_tw_run()` in `io_uring/tw.h`.
- `io_req_local_work_add()`: there is no nr_tw field, no IO_CQ_WAKE_FORCE
  and no `try_cmpxchg()` loop; it pushes with `mpscq_push()` and then counts
  `cq_wait_nr` down.
- `IO_CQ_WAKE_INIT`: defined as `(-1)` in `io_uring/wait.h`; `cq_wait_nr` is
  compared as a signed `int`.
- `cq_wait_nr` values:

| Value | Meaning |
|---|---|
| `IO_CQ_WAKE_INIT` | no waiter, or a forced add has claimed the wake |
| 0 | the lazy countdown reached zero and the wake was issued |
| above 0 | number of lazy adds still needed before the wake |

- Wake decision in `io_req_local_work_add()`, in order:
  1. `cq_wait_nr <= 0`: return, no wake.
  2. Add with `IOU_F_TWQ_LAZY_WAKE` (cleared first for a request with
     `IO_REQ_LINK_FLAGS`): `atomic_dec_and_test()`; wake only when it
     reaches zero.
  3. Add without it: `atomic_xchg()` to `IO_CQ_WAKE_INIT`; wake only when
     the old value was above 0.
- One wake per arming: after the wake `cq_wait_nr` is 0 or below, so later
  adds do not wake until the waiter arms it again.
- Early wake: a producer delayed between its push and the countdown can
  count down a later wait cycle; the waiter must recheck, as the loop in
  `io_cqring_wait()` does.
- Arming `cq_wait_nr`: `io_cqring_wait()` in `io_uring/wait.c` and
  `io_loop_wait_start()` in `io_uring/loop.c` store the count before
  `set_current_state()`; `io_cqring_min_timer_wakeup()` and
  `io_uring_try_cancel_requests()` store 1 followed by `smp_mb()`.
