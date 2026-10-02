- `mpscq_push()`: usable from task, softirq and hardirq context; it is one
  `xchg()` on `tail` plus one `WRITE_ONCE()`, takes no lock and never retries.
- `mpscq_push()` return value: `true` when the queue was empty before the
  push; `io_req_normal_work_add()` notifies the task only then;
  `io_req_local_work_add()` sets `IORING_SQ_TASKRUN` and signals the eventfd
  only then, but decides the wake from `cq_wait_nr` on every add.
- Consumers: one at a time, serialised by the caller; `mpscq_pop()` and
  `mpscq_pop_emptied()` have no protection of their own.
- `task_list` consumers: no lock; `tctx_task_work_run()` is called by the
  task that owns the tctx, or by `io_tctx_fallback_work()`, which
  `io_fallback_tw()` queues only after `task_work_add()` failed.
- `mpscq_pop()` returning NULL: either the queue is empty, or a producer has
  swapped `tail` and not yet linked its node; `mpscq_empty()` is false in the
  second case.
- **Potentially unsafe usage**: treating NULL from `mpscq_pop()` as "queue
  empty".
  - Unsafe: when the consumer then sleeps or tears down without testing
    `mpscq_empty()`; an entry already pushed is left unrun.
  - Safe: test `mpscq_empty()` after NULL and retry while it is false, as
    `tctx_task_work_run()` does.
  - Safe: stop on NULL and let the caller re-test `io_local_work_pending()`,
    as `__io_run_local_work_loop()` and `io_run_local_work_continue()` do.
- **Potentially unsafe usage**: retrying `mpscq_pop()` in a loop after NULL.
  - Unsafe: when the loop cannot be preempted or holds something the
    producer needs; the producer may have been preempted between its two
    stores and the loop never ends.
  - Safe: `cond_resched()` between attempts in process context, as
    `io_cancel_local_task_work()` and `__io_run_local_work()` do;
    `tctx_task_work_run()` also drops `ctx->uring_lock` first through
    `ctx_flush_and_put()`.
- `tctx_task_work_run()`: stops after a pop for which `mpscq_pop_emptied()`
  is true; the next `mpscq_push()` returns `true` and
  `io_req_normal_work_add()` calls `task_work_add()` again.
