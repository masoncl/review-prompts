- `io_disarm_next()` and `io_timeout_cancel()`: entered with `completion_lock`
  held, take `timeout_lock` inside.
- `io_kill_timeout()`: takes no lock and posts nothing; it cancels the timer,
  bumps `cq_timeouts` and moves the entry to the caller's local list.
- `io_flush_killed_timeouts()`: queues the completions with
  `io_req_queue_tw_complete()`, after `timeout_lock` is dropped.
- Sections under `timeout_lock`: none posts a CQE or queues task work;
  `io_timeout_fn()` and `io_link_timeout_fn()` unlock before
  `io_req_task_work_add()`.
- `hrtimer_try_to_cancel()` returning -1: the callback owns the request.
  `io_kill_timeout()` leaves it on `timeout_list`; `io_timeout_extract()`
  returns `-EALREADY`.
- Link chains: walking `link` of a request with `REQ_F_LINK_TIMEOUT` needs
  `timeout_lock`, because `io_link_timeout_fn()` edits the chain; see
  `io_match_task_safe()` and `io_prep_async_link()`.
- **Unsafe usage**: taking `completion_lock`, any other `spinlock_t` or a
  mutex while holding `timeout_lock`, a `raw_spinlock_t` taken with
  interrupts off.
  - Safe: take `completion_lock` first, as `io_kill_timeouts()` does.
  - Safe: collect under `timeout_lock`, act after unlock, as
    `io_flush_timeouts()` does.
- **Unsafe usage**: `hrtimer_cancel()` on a timeout timer while holding
  `timeout_lock`; `io_timeout_fn()` and `io_link_timeout_fn()` take the lock.
  - Safe: `hrtimer_try_to_cancel()` and handle -1, as `io_kill_timeout()`
    does.
