- Runqueue lock: the field is `__lock` in `struct rq`; there is no field named
  lock. Reach it through `rq_lockp()` or `__rq_lockp()`.
- Class order, highest first: `stop_sched_class`, `dl_sched_class`,
  `rt_sched_class`, `fair_sched_class`, `ext_sched_class`,
  `idle_sched_class`. `ext_sched_class` is below fair, not above it.
- `for_each_active_class()`: skips `fair_sched_class` when
  `scx_switched_all()`, and skips `ext_sched_class` when `scx_enabled()` is
  false. `for_each_class()` skips nothing.
- Changing class, priority, group or affinity: there is no
  check_class_changed() or __setscheduler_prio() here. `sched_change_begin()`
  and `sched_change_end()` in `kernel/sched/core.c` bracket the change.
- `curr` and `h_curr` in `struct cfs_rq`: `rq->cfs.curr` is the entity of the
  picked task, `rq->donor`. `h_curr` is set at every level of the hierarchy,
  to the entity on the running path at that level.
- `struct cfs_tg_state`: besides the queue and the group entity it holds the
  group entity's statistics, a `struct sched_statistics`;
  `__schedstats_from_se()` in `kernel/sched/stats.h` reaches them from the
  entity.
- Group entity lookup: `tg_se()` or `cfs_rq_se()`. Both return `NULL` for
  `root_task_group`, whose per-CPU queue is `rq->cfs` itself.
- `struct task_group`, RT side: still per-CPU pointer arrays, `rt_se` and
  `rt_rq`. When `rt_group_sched_enabled()` is false, `set_task_rq()` attaches
  every task to the arrays of `root_task_group`.
- CFS bandwidth: `throttle_cfs_rq()` marks the hierarchy and removes no
  entity. Each task dequeues itself in `throttle_cfs_rq_work()`, on return to
  user space, and waits on `throttled_limbo_list` of its `struct cfs_rq`.
- A throttled task: `p->throttled` is set and `p->se.on_rq` is 0, but
  `p->on_rq` is unchanged, since `dequeue_task_fair()` is called directly. So
  `task_on_rq_queued()` is true for a task that is in no tree.
- `CONFIG_SCHED_PROXY_EXEC`: depends on `!SCHED_CLASS_EXT` and `!PREEMPT_RT`
  in `init/Kconfig`. A kernel with `rq->donor` distinct from `rq->curr` never
  has `ext_sched_class`.
- DL servers: each is a `struct sched_dl_entity` embedded in `struct rq`, with
  no task behind it.
- `dl_server` in `struct rq` and in `struct task_struct`: `__pick_task_dl()`
  records in the runqueue which server picked the task;
  `put_prev_set_next_task()` moves that to the picked task.
- `struct scx_sched` in `kernel/sched/ext/internal.h`: one loaded BPF
  scheduler. `struct sched_ext_ops` is embedded in it, in a union with
  `struct sched_ext_ops_cid`.
- With `CONFIG_EXT_SUB_SCHED` there can be several `struct scx_sched`: the
  root one, `scx_root`, and children attached to cgroups. `p->scx.sched` names
  the one that owns a task; `sched` in `struct scx_dispatch_q` names the one
  that owns a DSQ, and is `NULL` for the per-runqueue reject and rescue DSQs.
- `struct sched_cache_group` (`CONFIG_SCHED_CACHE`): one per
  `struct mm_struct`, refcounted. Each task of that mm holds its own
  reference in `sched_cache_grp`. It carries the preferred CPU of the process
  for cache-aware balancing.
- `struct sched_domain_shared`: not only on the LLC domain. On asymmetric
  capacity it is also attached to the lowest `SD_ASYM_CPUCAPACITY_FULL`
  domain that is not a NUMA domain. `sd_balance_shared` points to that one if
  it exists, else to the LLC one. See `update_top_cache_domain()` in
  `kernel/sched/topology.c`.
- Callers of `move_queued_task_locked()`, for example push and pull in RT and
  deadline, hold both runqueue locks.
