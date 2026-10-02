- Storage: `struct task_group` has a `__percpu` `cfs_rq` pointer and no `se`
  array; entity and runqueue sit together in `struct cfs_tg_state`.
- Accessors: `tg_cfs_rq()`, `tg_se()` and `cfs_rq_se()` in
  `kernel/sched/sched.h`; `tg_se()` returns NULL for the root group.
- A group entity is never in an rbtree and never picked.
- Group entity `vruntime`, `deadline`, `slice`: not maintained;
  `update_curr()` returns before the vruntime update for a non-task entity.
- Group entity is used for: its `load.weight` (input to
  `__calc_prop_weight()`), PELT propagation, `on_rq` accounting in the
  parent's `load` and `nr_queued`, and the `parent` chain that the per-level
  walks follow.
- `cfs_rq->h_curr`: the running entity of each level, set by
  `set_next_entity()`; `update_curr()`, `throttle_cfs_rq()` and
  `kernel/sched/pelt.c` read it.
- `cfs_rq->curr` and `cfs_rq->next`: set only on `rq->cfs`, always to a task
  entity; see `set_next_task_fair()` and `set_next_buddy()` callers.
- A group's `struct cfs_rq`: its `tasks_timeline`, `sum_w_vruntime` and
  `sum_weight` stay empty.
- A group's `struct cfs_rq` holds: `load`, the four counters, `h_curr`,
  `avg`, `h_load`, bandwidth state and `throttled_limbo_list`.
- `sched_delayed`: set only on task entities; the only caller of
  `set_delayed()` is `__dequeue_task()`, with `&p->se`.
- `dequeue_hierarchy()`: stops dequeueing parents once a level's
  `cfs_rq->load.weight` is non-zero; there is no dequeue_entities() here.
