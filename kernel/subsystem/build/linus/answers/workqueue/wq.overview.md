- Non-ordered unbound workqueue: has one pwq per possible CPU plus `dfl_pwq`,
  not one per pod; CPUs of one pod share a `struct worker_pool`, not a pwq.
  See `apply_wqattrs_prepare()` and `get_unbound_pool()` in
  `kernel/workqueue.c`.
- `dfl_pwq`: spans the whole effective cpumask; `unbound_wq_update_pwq()`
  installs it in a CPU's slot when it cannot allocate a pwq.
- Ordered workqueue: every `cpu_pwq` slot and `dfl_pwq` hold the same pwq.
- Ordered workqueue during an attrs or unbound-cpumask change: has several
  pwqs on `wq->pwqs`; the new one is `plugged` and runs nothing until every
  older pwq is released and `pwq_release_workfn()` calls
  `unplug_oldest_pwq()`.
- `max_active` on a per-CPU or BH pool (`is_percpu_pool()` true): compared
  with `pwq->nr_active`.
- `struct wq_node_nr_active`: `nr` is an `atomic_t` that no single lock
  serialises; `lock` covers `pending_pwqs` and nests inside `pool->lock`.
- BH workqueue: has no `max_active` limit; `__alloc_workqueue()` stores
  `INT_MAX`.
- Per-CPU and BH pools: static per-CPU arrays (`cpu_worker_pools`,
  `bh_worker_pools`) set up in `workqueue_init_early()`; only unbound pools
  are created on demand.
- Concurrency management (`pool->nr_running`): applies only to per-CPU kthread
  pools while bound to their CPU.
- Unbound and BH pools: always `POOL_DISASSOCIATED`, so their workers carry
  `WORKER_UNBOUND` and `need_more_worker()` is true whenever the worklist is
  not empty.
- BH pool: has one `struct worker` with `task` NULL, created for every
  possible CPU in `workqueue_init()`; `workqueue_softirq_action()` runs it
  from `tasklet_action()` and `tasklet_hi_action()` in `kernel/softirq.c`.
- Unbound pool identity: `nice`, `affn_strict`, `__pod_cpumask`, and `cpumask`
  only when `affn_strict` is clear; see `wqattrs_equal()`.
- `affn_scope` and `ordered`: belong to the workqueue only; `wqattrs_equal()`
  does not compare them and `wqattrs_clear_for_pool()` resets them in a
  pool's attrs, so an ordered workqueue can share a pool with non-ordered
  ones.
- `WQ_PERCPU`: marks a per-CPU workqueue.
- `mayday_cursor`: a dummy `struct work_struct` in every pwq that
  `assign_rescuer_work()` leaves on `pool->worklist` to mark its position, so
  a worklist entry is not always a real work item; `assign_work()` removes it
  and returns `false`.
- `pwq_release_worker`: a `struct kthread_worker` that workqueue itself uses;
  `put_pwq()` queues `release_work` on it when the refcount reaches zero,
  because the pwq cannot be released under `pool->lock`.
