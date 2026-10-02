- Arming points of `throttle_cfs_rq_work()`: `throttle_cfs_rq()`, on
  `rq->donor` only and only when `cfs_rq->h_curr` is on_rq; and
  `set_next_task_fair()`, when `account_cfs_rq_runtime()` reports a
  throttled level.
- `pick_task_fair()`: arms nothing and skips nothing; a queued task of a
  throttled group stays in the `rq->cfs` tree and can be picked.
- There is no check_cfs_rq_runtime() here; `__account_cfs_rq_runtime()`
  calls `throttle_cfs_rq()`.
- `throttle_cfs_rq()`: returns false without throttling when
  `__assign_cfs_rq_runtime()` obtains runtime.
- `task_throttle_setup_work()`: does nothing for `PF_KTHREAD` or
  `PF_EXITING` tasks, so a kernel thread in a throttled group is never
  dequeued by the throttle.
- `throttle_cfs_rq_work()`: takes the rq lock itself; returns early if the
  task is exiting, left the fair class, or `throttle_count` is 0.
- Limbo list: the one of the task's own `cfs_rq_of()`, which may be a
  descendant of the runqueue that ran out of quota.
- `tg_unthrottle_up()`: stops re-enqueueing as soon as `throttle_count` is
  non-zero again and splices the rest back onto the limbo list.
- `enqueue_throttled_task()`: puts the task straight on the limbo list only
  if the target is in a throttled hierarchy and the task is not the current
  donor; otherwise it clears `p->throttled` and the normal enqueue follows.
- `dequeue_throttled_task()` with `DEQUEUE_SLEEP`: unlinks and clears
  `p->throttled`.
- `dequeue_throttled_task()` without `DEQUEUE_SLEEP`: unlinks, keeps
  `p->throttled`, and calls `detach_task_cfs_rq()` if the task is migrating.
