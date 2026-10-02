- Locks asserted: only `lockdep_assert_rq_held(task_rq(p))`, in both
  `sched_change_begin()` and `sched_change_end()`; `p->pi_lock` is not
  asserted.
- Clock: begin calls `update_rq_clock()` itself unless `DEQUEUE_NOCLOCK` is
  passed, then forces `DEQUEUE_NOCLOCK` for both sides.
- Flags: begin adds nothing but `DEQUEUE_NOCLOCK`; the caller passes
  `DEQUEUE_SAVE`.
- "Running" means `task_current_donor()`, not `task_current()`.
- `ctx->queued`: sampled after `switching_from`, so a `sched_delayed` fair
  task that `switching_from_fair()` dequeued is not re-enqueued by end.
- `switched_from`: called in begin, after the dequeue and the put; end calls
  `switching_to`, the enqueue, the set, then `switched_to`.
- `prio_changed`: called by end with no NULL test whenever `ENQUEUE_CLASS` is
  clear, also when nothing about the priority changed; the old value comes
  from `get_prio` if the class has one (dl: the deadline).
- End with `ENQUEUE_CLASS`: reschedules or raises `rq->next_class` only if
  `ctx->running`; a queued, not running task relies on `switched_to`.
- `set_cpus_allowed_force()`: takes only the rq lock, with `__task_rq_lock`.
- Balance callbacks: `prio_changed`, `switched_from` and `switched_to` may
  queue them; the caller runs them before unlock, as `rt_mutex_setprio()`
  does with `__balance_callbacks()`, or splices them off before unlock, as
  `__sched_setscheduler()` does with `splice_balance_callbacks()`;
  `assert_balance_callbacks_empty()` warns under `CONFIG_PROVE_LOCKING`
  otherwise.
- **Potentially unsafe usage**: a `sched_change` scope under the rq lock
  alone.
  - Unsafe: when the scope writes a field read under `p->pi_lock` alone, such
    as `p->sched_class`, which `select_task_rq()` reads after asserting only
    `p->pi_lock`.
  - Safe: an empty scope that writes no attribute, as `scx_bypass()` in
    `kernel/sched/ext/ext.c` does.
- **Potentially unsafe usage**: writing `p->prio` under `DEQUEUE_SAVE`
  without `DEQUEUE_MOVE`.
  - Unsafe: when `p` is in `rt_sched_class` and the value changes;
    `move_entity()` leaves the entity on the list of the old priority.
  - Safe: when the rt or dl priority cannot change, as in `set_user_nice()`,
    which returns early for rt and dl policy and whose `effective_prio()`
    keeps a boosted `p->prio`.
- **Unsafe usage**: passing an enqueue-only flag to `sched_change_begin()`;
  it warns on `flags & 0xFFFF0000`.
  - Safe: OR `ENQUEUE_HEAD` or `ENQUEUE_REPLENISH` into `scope->flags` inside
    the scope, as `rt_mutex_setprio()` does.
- **Unsafe usage**: changing `p->sched_class` in a scope opened without
  `DEQUEUE_CLASS`; `sched_change_end()` warns and no switch callback runs.
  - Safe: compare with `__setscheduler_class()` first and add
    `DEQUEUE_CLASS`, as `__sched_setscheduler()` does.
- **Unsafe usage**: opening a second scope before the first has ended; the
  context is one per-CPU `struct sched_change_ctx` and begin overwrites it.
  - Safe: one scope at a time under the rq lock, as `sched_move_task()` does.
- **Potentially unsafe usage**: writing `p->sched_class` outside a scope.
  - Unsafe: once the task can be queued or be the donor of a runqueue; core
    `dequeue_task()` then calls the new class for a task the old class
    queued.
  - Safe: in `sched_fork()`, where `__sched_fork()` has set `p->on_rq` to 0
    and `wake_up_new_task()` has not yet run.
