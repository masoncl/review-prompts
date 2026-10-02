- Checks in `set_task_cpu()`: unconditional `WARN_ON_ONCE()` calls. There is
  no CONFIG_SCHED_DEBUG option in this tree. Only the lock check is
  conditional, on `CONFIG_LOCKDEP` and `debug_locks`.
- Lock check: tests `p->pi_lock` or `__rq_lockp(task_rq(p))`, where
  `task_rq(p)` is still the old runqueue.
- Queued-but-not-migrating check: applies to `fair_sched_class` tasks in
  `TASK_RUNNING` only.
- Migration-disabled check: suppressed when `proxy_migrated` is true, that is
  `sched_proxy_exec()`, `p->is_blocked` and `task_cpu(p) != p->wake_cpu`.
- `set_task_cpu()` makes no test of `p->cpus_ptr` against `new_cpu`.
- Unchanged CPU: `trace_sched_migrate_task()` and `__set_task_cpu()` still
  run. Only the `p->sched_class->migrate_task_rq` callback,
  `p->se.nr_migrations` and `perf_event_task_migrate()` are skipped.
- `set_task_cpu()` calls no rseq or mm_cid hook itself; there is no
  rseq_migrate() here. `__set_task_cpu()` calls
  `rseq_sched_set_ids_changed()`.
- New tasks: `sched_cgroup_fork()` and `wake_up_new_task()` call
  `__set_task_cpu()` under `p->pi_lock`, not `set_task_cpu()`, so the
  `migrate_task_rq` callback and the checks do not run.
- `proxy_set_task_cpu()` under `CONFIG_SCHED_PROXY_EXEC`: calls
  `__set_task_cpu()` and restores `p->wake_cpu`. `proxy_migrate_task()` uses
  it to move a blocked task, possibly to a CPU outside `p->cpus_ptr`.
- Helper choice for a queued task:

| Helper | Locks on entry | Locks on return |
|---|---|---|
| `move_queued_task()` | source runqueue | destination runqueue only |
| `move_queued_task_locked()` in `kernel/sched/sched.h` | both runqueues | both runqueues |

- **Potentially unsafe usage**: `set_task_cpu()` on a task whose `p->on_rq` is
  `TASK_ON_RQ_QUEUED`.
  - Unsafe: with one runqueue lock held. `_task_rq_lock()` relies on
    `task_on_rq_migrating()` to reject a task in flight. For a fair task in
    `TASK_RUNNING` `set_task_cpu()` warns in any case.
  - Safe: call `deactivate_task()` first, which sets
    `TASK_ON_RQ_MIGRATING`, as `move_queued_task()` and `detach_task()` do.
  - Safe: a non-fair task with `p->pi_lock` and both runqueue locks held, as
    `dl_task_offline_migration()` called from `dl_task_timer()`.
