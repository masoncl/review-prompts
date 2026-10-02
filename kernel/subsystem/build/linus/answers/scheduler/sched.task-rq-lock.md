- `task_rq_lock()` and `__task_rq_lock()`: macros in `kernel/sched/sched.h`.
  The bodies are `_task_rq_lock()` and `___task_rq_lock()` in
  `kernel/sched/core.c`.
- `___task_rq_lock()`: requires `p->pi_lock`; it opens with
  `lockdep_assert_held(&p->pi_lock)`.
- `p->pi_lock` alone: keeps `task_cpu()` stable only while `p->on_rq` is 0.
  A queued task is moved under the runqueue lock alone, as `detach_task()`
  in `kernel/sched/fair.c` does.
- Runqueue lock alone: keeps `task_cpu()` stable only while `p->on_rq` is
  non-zero. After `__block_task()` stores 0 for a task that is not on a CPU,
  `try_to_wake_up()` can move the task under `p->pi_lock` alone; a caller
  that does not hold `p->pi_lock` must not touch `p` afterwards.
- `p->on_cpu`: written by `prepare_task()` and `finish_task()` under the
  runqueue lock. `p->pi_lock` does not cover it.
- **Potentially unsafe usage**: locking `task_rq(p)` and then treating `p` as
  being on that runqueue, with no test after the lock is taken.
  - Unsafe: when the task can be queued or woken meanwhile. The task may have
    moved, or be `TASK_ON_RQ_MIGRATING`, before the lock is held.
  - Safe: under `p->pi_lock` for a task in `TASK_WAKING` that is off the
    runqueue, as `migrate_task_rq_dl()` does. `try_to_wake_up()`, which
    holds `p->pi_lock`, changes the CPU of such a task.
  - Safe: take `p->pi_lock` and a known runqueue lock, then test
    `task_rq(p) == rq`, as `migration_cpu_stop()` and `push_cpu_stop()` do.
  - Safe: `task_rq_lock()`, which re-tests after it locks.
