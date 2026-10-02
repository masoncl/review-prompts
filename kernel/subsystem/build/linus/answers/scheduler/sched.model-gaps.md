- Models do not know `rq->next_class`. On the `pick_task_fair()` and
  `pick_task_scx()` paths `rq_modified_begin()` runs before the rq lock is
  dropped, and the pick returns `RETRY_TASK` if `rq_modified_above()` is true
  afterwards; see `sched_balance_newidle()` and `do_pick_task_scx()`.
- Models take the balance pass to start at the class of `prev`.
  `prev_balance()` starts at the class of `rq->donor`.
- Models believe check_class_changed() still runs after a class change.
  `sched_change_end()` calls `prio_changed` when `ENQUEUE_CLASS` is clear,
  without a NULL test, so every class defines it.
- Models may read `cid_on_cpu()` in `kernel/sched/sched.h` as sched_ext code.
  It tests a bit of the mm concurrency id under `CONFIG_SCHED_MM_CID`,
  unrelated to `kernel/sched/ext/cid.c`.
- Models set `p->sched_contributes_to_load` in `try_to_block_task()`.
  `block_task(rq, p, task_state)` sets it.
- Models expect `resched_curr()` when fair preempts at the end of a slice or
  on a wakeup. `update_curr()` and `wakeup_preempt_fair()` call
  `resched_curr_lazy()`.
- Models do not expect lock annotations. Functions carry
  `__must_hold(__rq_lockp(rq))` and the like, and `kernel/sched/Makefile` sets
  `CONTEXT_ANALYSIS_core.o`.
- Models take `HRTICK` to default off. `kernel/sched/features.h` turns it and
  `HRTICK_DL` on under `CONFIG_HRTIMER_REARM_DEFERRED`.
