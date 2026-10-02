- `ttwu_runnable()` in `kernel/sched/core.c`: tests `p->se.sched_delayed` and
  calls `proxy_needs_return()` only inside `if (p->is_blocked)`.
- A queued task that is delayed or proxy-migrated must therefore have
  `p->is_blocked == 1` when the rq lock is released.
- With `p->is_blocked == 0` the waker skips both and sets `TASK_RUNNING`: a
  delayed task stays delayed and a later `pick_next_entity()` that selects it
  dequeues it.
- `p->on_rq == 0` with `p->on_cpu == 0`: the waker moves and enqueues `p`
  without the old rq lock, so `rq->donor` and the class curr pointers must
  not point at `p` when `__block_task()` stores 0.
- `proxy_deactivate()`: calls `proxy_resched_idle()` before `block_task()` for
  that reason; the task is not `rq->curr` and not `on_cpu`, so nothing else
  holds the waker off.
- `proxy_migrate_task()`: releases the rq lock with
  `p->on_rq == TASK_ON_RQ_MIGRATING`, `task_cpu(p)` already the target, and
  `p` on no runqueue. Safe because `__task_rq_lock()` in `ttwu_runnable()`
  spins while `task_on_rq_migrating()`, and `proxy_resched_idle()` ran first.
- `sched_balance_newidle()`, called from the pick in `__schedule()`: releases
  the rq lock while prev has `on_rq == 0` and is still `rq->curr`. Safe
  because `on_cpu` is 1 until `finish_task()`; the waker queues on the wake
  list or spins on `p->on_cpu`.
- `finish_task()` clears `on_cpu` before `finish_lock_switch()` releases the
  lock, so the context switch itself is not such a path.
