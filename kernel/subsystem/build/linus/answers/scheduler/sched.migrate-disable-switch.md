- Call site: `__schedule()` calls `migrate_disable_switch()` for `prev` after
  `local_irq_disable()` and `rcu_note_context_switch()`, before `rq_lock()`.
  The runqueue lock is not held on entry.
- Locks: it takes `p->pi_lock` and the runqueue lock itself with
  `scoped_guard (task_rq_lock, p)`, and drops both before returning.
- It runs on every entry to `__schedule()`, whether or not `prev` is then
  switched out.
- Change: `do_set_cpus_allowed()` with `SCA_MIGRATE_DISABLE` and
  `cpumask_of(rq->cpu)`. There is no __do_set_cpus_allowed() in this tree.
- `set_cpus_allowed_common()` with `SCA_MIGRATE_DISABLE` or
  `SCA_MIGRATE_ENABLE`: writes `p->cpus_ptr` and returns.
  `p->nr_cpus_allowed`, `p->cpus_mask` and `p->user_cpus_ptr` keep their
  values.
- Between `migrate_disable()` and the next `__schedule()`: `p->cpus_ptr`
  still equals `&p->cpus_mask`.
- **Potentially unsafe usage**: deciding that a task may be moved from
  `p->nr_cpus_allowed` or `p->cpus_ptr` alone.
  - Unsafe: from `p->nr_cpus_allowed`, which migration disable never changes,
    or from `p->cpus_ptr` of a task that may be on a CPU; `set_task_cpu()`
    warns for a migration-disabled task.
  - Safe: from `p->cpus_ptr` of a task that is not on a CPU, since it has
    passed `migrate_disable_switch()`; `can_migrate_task()` in
    `kernel/sched/fair.c` also rejects `task_on_cpu()`.
  - Safe: test `is_migration_disabled()` as well, as `select_task_rq()` does;
    `get_push_task()` tests `p->migration_disabled`.
  - Safe: test `is_migration_disabled()` before the mask, as
    `task_can_run_on_remote_rq()` in `kernel/sched/ext/ext.c` does.
