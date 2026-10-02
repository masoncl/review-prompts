- Boot parameter `sched_proxy_exec`, static key `__sched_proxy_exec`
  (default true, defined under `CONFIG_SCHED_PROXY_EXEC`), test
  `sched_proxy_exec()`; see `setup_proxy_exec()` in `kernel/sched/core.c`.
- `__schedule()` calls `find_proxy_task()` when `next->is_blocked` is set, not
  when `next->blocked_on` is set; the walk loops while `p->is_blocked`.
- `p->blocked_on`: guarded by `p->blocked_lock`, which
  `__set_task_blocked_on()` and `__clear_task_blocked_on()` assert;
  `clear_task_blocked_on()` clears it without the mutex `wait_lock`.

| Step in `find_proxy_task()`, for chain task `p` | `rq->curr` in chain | Otherwise |
|---|---|---|
| `p->blocked_on` is NULL, or mutex has no owner | only if `p` itself is `rq->curr`: clear `p->is_blocked`, return `p` | `proxy_deactivate(rq, p)`, return NULL |
| `owner->on_rq` is 0, or `sched_delayed` | `proxy_resched_idle()` | clear `p->blocked_on`, `proxy_deactivate(rq, p)` |
| owner on another CPU | `proxy_resched_idle()` | `proxy_migrate_task()` to the owner's CPU, return NULL |

- `proxy_migrate_task()`: moves `p`, the chain task whose owner is remote,
  which need not be the donor.
- `proxy_migrate_task()` sequence: `proxy_resched_idle()`,
  `deactivate_task()`, `proxy_set_task_cpu()`, drop the rq lock,
  `attach_one_task()` on the target, retake the lock.
- Return migration: on wakeup `proxy_needs_return()` sees
  `task_cpu(p) != p->wake_cpu`, dequeues `p` unless it is `rq->curr`, and
  `try_to_wake_up()` places it with `select_task_rq()` starting from
  `p->wake_cpu`.
- `find_proxy_task()` returning `rq->idle`: `__schedule()` jumps to
  `keep_resched` and switches to idle with need-resched set, so the pick is
  retried.
