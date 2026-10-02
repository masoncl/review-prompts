- `update_se()` in `kernel/sched/fair.c`: charges `sum_exec_runtime`,
  thread-group runtime and `cgroup_account_cputime()` to `rq->curr`; vruntime,
  deadline and RT/DL runtime are charged to the donor's entity.
- `wakeup_preempt()` in `kernel/sched/core.c`: chooses the hook by comparing
  `p->sched_class` with `rq->next_class`, not with `rq->donor->sched_class`;
  the class hooks then compare priority or deadline with `rq->donor`.
- `rq->next_class`: set in `__schedule()` from the picked task before
  `find_proxy_task()` runs; `proxy_resched_idle()` sets it to
  `idle_sched_class`.
- There is no proxy_tag_curr() here. `pick_next_pushable_task()` and
  `pick_next_pushable_dl_task()` skip a task that is `task_on_cpu()`;
  `enqueue_task_rt()`, `put_prev_task_rt()` and the deadline equivalents skip
  the pushable list for a task with `task_is_blocked()`.
- `rq->donor != rq->curr` is also visible inside `__schedule()`:
  `proxy_migrate_task()` sets the donor to `rq->idle` and drops the rq lock
  while `rq->curr` is still the previous task.
- `proxy_reset_donor()`: called from the wakeup path
  (`proxy_needs_return()`), sets `rq->donor` back to `rq->curr` and
  reschedules, so a split can end outside `__schedule()`.
