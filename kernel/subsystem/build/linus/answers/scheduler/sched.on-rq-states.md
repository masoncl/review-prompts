- `p->is_blocked`: exists, `u8` in `struct task_struct`
  (`include/linux/sched.h`), present with or without
  `CONFIG_SCHED_PROXY_EXEC`.

| `p->is_blocked` | Meaning | Written by | Lock |
|---|---|---|---|
| 1 | task entered `__schedule()`, not as a preemption, with a sleeping `__state`, no pending signal, and has not been woken | `try_to_block_task()`, before it decides whether to dequeue | rq lock |
| 0 | woken, or never blocked | `ttwu_do_wakeup()`; `find_proxy_task()` for `rq->curr` | rq lock; none when `try_to_wake_up()` wakes `current` |

- `p->is_blocked == 1` with `p->on_rq == 1`: the task stayed queued, either
  delayed (`p->se.sched_delayed`) or mutex-blocked under proxy execution.
- `p->is_blocked` is not `task_is_blocked()`: `task_is_blocked()` in
  `kernel/sched/sched.h` tests `p->blocked_on` and `sched_proxy_exec()`.
- `p->blocked_on` set with `p->is_blocked == 0`: a task preempted in the mutex
  slow path before it blocked, or woken without its `blocked_on` being
  cleared; it is picked and runs itself.
- `p->on_rq`: changes under the rq lock alone; `p->pi_lock` is not required
  (`block_task()` from `__schedule()`, `deactivate_task()`).
- `p->on_cpu`: an unconditional `u8`, not limited to SMP builds.
- `task_is_runnable()` in `include/linux/sched.h`: the helper for "is
  runnable"; `task_on_rq_queued()` is not, it is true for a delayed task.
- `task_is_runnable()` does not test `p->is_blocked`: it returns true for a
  mutex-blocked task that proxy execution kept on the runqueue.
