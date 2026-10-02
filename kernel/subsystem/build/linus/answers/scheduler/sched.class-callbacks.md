- `struct sched_class` has no member named after `pick_next_task()` and there
  is no pick_next_task_fair function; the fast path in `__pick_next_task()`
  calls `pick_task_fair()` directly and is skipped when `scx_enabled()`.
- `pick_task(rq, rf)`: takes `struct rq_flags *`; returns a task, NULL or
  `RETRY_TASK`.
- `pick_task` may drop the rq lock: `pick_task_fair()` through
  `sched_balance_newidle()`, `pick_task_scx()` through dispatch; both can
  return `RETRY_TASK`, and the core then restarts from the highest class.
- `pick_task_fair()`: can finish the delayed dequeue of the entity it picked
  and pick again; that task is then off the runqueue.
- `balance(rq, rf)`: two arguments; a search for `.balance` shows stop, dl, rt
  and idle define it, fair and ext do not.
- `prev_balance()`: not called on the fair fast path of
  `__pick_next_task()`.
- `enqueue_task` and `dequeue_task`: the class itself calls
  `add_nr_running()` and `sub_nr_running()`; core `enqueue_task()` and
  `dequeue_task()` do not touch `rq->nr_running`.
- `dequeue_task`: returns `bool`; `sched_change_begin()` and
  `deactivate_task()` ignore the result, only `block_task()` acts on it.
- `p->on_rq`: written by `activate_task()` and `deactivate_task()`, not by
  core `enqueue_task()`; `deactivate_task()` sets `TASK_ON_RQ_MIGRATING` and
  warns on `DEQUEUE_SLEEP`.
- `__block_task()`: called by core `block_task()` when the class returns
  `true`; fair calls it itself only when it completes a dequeue with
  `DEQUEUE_DELAYED`; after it the class must not touch `p`.
- `put_prev_task`: also called for a task the class has already dequeued, as
  in `sched_change_begin()`; the class tests its own queued state, as
  `put_prev_task_fair()` does with `se->on_rq`.
- `put_prev_task` with `next == p`: `__schedule()` calls it so, followed by
  `set_next_task` with `first` true, when the donor is unchanged and
  `prev != next` under `sched_proxy_exec()`.
- `set_next_task`: `sched_change_end()` calls it whenever `ctx->running`,
  whether or not the task was re-enqueued.
- Task handed to `put_prev_task`: `rq->donor`, not `rq->curr`; the
  `put_prev_task()` helper and `put_prev_set_next_task()` warn if
  `rq->donor != prev`.
- Task handed to `set_next_task` from the pick: the picked task, which
  `__schedule()` makes `rq->donor` afterwards.
