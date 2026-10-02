- `sched_class_above(_a, _b)`: `((_a) < (_b))`; the lower address is the
  higher class, and `SCHED_DATA` places stop first, at
  `__sched_class_highest`.
- Comment above `DEFINE_SCHED_CLASS()` in `kernel/sched/sched.h`: says the
  classes are laid out in reverse order; the linker script and the
  `BUG_ON()`s in `sched_init()` show highest first.
- `wakeup_preempt()` in `kernel/sched/core.c`: compares `p->sched_class` with
  `rq->next_class`, not with the class of `rq->curr`; it calls
  `rq->next_class->wakeup_preempt` both for an equal and for a higher class,
  and for a higher class also calls `resched_curr()` and raises
  `rq->next_class`.
- `rq->next_class`: set to the class of the picked task in `__schedule()`;
  raised by `wakeup_preempt()` and by `sched_change_end()`.
- There is no check_class_changed() here; `sched_change_end()` does the class
  comparison.
- `next_active_class()`: skips `fair_sched_class` when `scx_switched_all()`,
  and skips `ext_sched_class` when `scx_enabled()` is false.
- `task_should_scx()` in `kernel/sched/ext/ext.c`: when `scx_enabled()` and
  `scx_switching_all` is set, returns true for every policy, so
  `SCHED_NORMAL`, `SCHED_BATCH` and `SCHED_IDLE` tasks map to ext.
- `task_should_scx()`: tests `scx_switching_all` before `SCX_DISABLING`, so a
  task still maps to ext during teardown while switch-all is set.
- `sched_fork()`: a second, open-coded copy of the mapping; it returns
  `-EAGAIN` for a `dl_prio()` child and never calls
  `__setscheduler_class()`.
- `scx_setscheduler_class()`: what `scx_root_enable_workfn()` and
  `scx_root_disable()` use to pick a task's new class; it returns
  `stop_sched_class` for a stop task and otherwise
  `__setscheduler_class(p->policy, p->prio)`.
- Changing a task into stop or idle through `sched_change`:
  `switching_to_stop()` and `switching_to_idle()` are `BUG()`.
