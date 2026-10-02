- `__dequeue_task()` in `kernel/sched/fair.c` makes the delay decision and
  returns false; `dequeue_entity()` returns void and never delays.
- dequeue_entities() and finish_delayed_dequeue_entity() are not defined
  here; `dequeue_hierarchy()` walks the levels and `__dequeue_task()` with
  `DEQUEUE_DELAYED` calls `__block_task()` last.
- `DEQUEUE_SPECIAL` or `DEQUEUE_THROTTLE` in the flags: no delay, even with
  `DEQUEUE_SLEEP` and an ineligible entity.
- `task_is_throttled(p)`: `dequeue_task_fair()` returns true before
  `__dequeue_task()` is reached.
- `DEQUEUE_SLEEP | DEQUEUE_DELAYED` is passed in three places:
  `pick_next_entity()`, `wait_task_inactive()` and `switching_from_fair()`.
- Migration and `DEQUEUE_SAVE`/`ENQUEUE_RESTORE` changes (affinity, nice,
  cgroup move) dequeue without `DEQUEUE_DELAYED`: `se.sched_delayed` stays
  set and the task is enqueued again still delayed.
- Nothing watches eligibility: a delayed task that is not woken leaves when
  `pick_next_entity()` selects it, or through `wait_task_inactive()` or
  `switching_from_fair()`.
- `pick_next_entity()` is also called from `wakeup_preempt_fair()`, so a
  delayed task can reach `p->on_rq == 0` during the wakeup of another task.
- **Potentially unsafe usage**: using `p` after `dequeue_task()` with
  `DEQUEUE_SLEEP | DEQUEUE_DELAYED`.
  - Unsafe: holding only the rq lock; `__block_task()` has stored
    `p->on_rq = 0` and `try_to_wake_up()` may be enqueuing `p` on another rq.
  - Safe: holding `p->pi_lock` as well, which `try_to_wake_up()` takes before
    it reads `p->on_rq`; `wait_task_inactive()` does so through
    `task_rq_lock()`.
