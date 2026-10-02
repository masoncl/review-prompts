- Rbtree: the task's entity goes into `rq->cfs.tasks_timeline`, whatever
  its group; `enqueue_task_fair()` calls `__enqueue_entity()` on `&rq->cfs`.
- `__enqueue_entity()` and `__dequeue_entity()`: warn if the runqueue is not
  `&rq->cfs` or the entity is not a task.
- `cfs_rq_of(se)`: still the group's runqueue, used for accounting only.
- `enqueue_hierarchy()`: walks every level to the root; `enqueue_entity()`
  there updates PELT, `load`, `nr_queued` and `on_rq`, inserts in no tree.
- A task that is `rq->cfs.curr` is placed but not inserted; `curr` stays
  outside the tree until `put_prev_task_fair()`.
- `pick_task_fair()`: one `pick_next_entity(rq, true)` on `rq->cfs`; it does
  not call `group_cfs_rq()` and does not descend.
- `se->h_load` of the task: the stored hierarchical weight; `se->load` stays
  the per-level weight (nice for a task, shares for a group entity).
- `calc_delta_fair()`, `avg_vruntime_weight()` callers and
  `hrtick_start_fair()` use `se->h_load`, not `se->load`.
- `__calc_prop_weight()`: its callers start from `NICE_0_LOAD`; at each level
  it multiplies by `se->load.weight` and divides by `cfs_rq->load.weight` (by
  `NICE_0_LOAD` at the top level), floor `MIN_SHARES` per level.
- `reweight_eevdf()`: applies the result to `se->h_load` and rescales lag,
  deadline and protection.
- `se->h_load` is refreshed only by callers of `reweight_eevdf()`, for example
  `enqueue_task_fair()`, `set_next_task_fair()` and `task_tick_fair()`; a
  queued task that is not running keeps a stale value in between.
- `reweight_entity()`: changes `se->load`, `cfs_rq->load` and the PELT load
  only; it does not touch `vruntime`, `vlag` or `deadline`.
- `calc_group_shares`: a static call, not a function; default
  `calc_concur_shares()`, which scales `tg->shares` by the smaller of
  `tg_tasks()` and `tg_cpus()`.
- `__sched_cgroup_mode_update()`: switches the static call from the debugfs
  file `cgroup_mode`; it selects one of five functions, `calc_concur_shares()`
  among them.
- `__calc_smp_shares()`: holds the load fraction formula; clamps to
  `MIN_SHARES`..`shares_max`, and `shares_max` can exceed `tg->shares`.
