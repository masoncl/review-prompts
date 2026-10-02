- `__migrate_disable()` and `__migrate_enable()`: inline in
  `include/linux/sched.h`. They change `rq->nr_pinned` through
  `this_rq_pinned()`. `migrate_disable()` in `kernel/sched/core.c` is the
  exported copy for modules.
- `___migrate_enable()` in `kernel/sched/core.c`: the slow path. It runs only
  when `p->cpus_ptr != &p->cpus_mask`, that is, only if the task entered
  `__schedule()` while disabled.
- `migrate_disable()` and `migrate_enable()` themselves do not block: the
  outermost calls run under `guard(preempt)()`. `__set_cpus_allowed_ptr()`
  with `SCA_MIGRATE_ENABLE` returns before `wait_for_completion()`.
- `task_cpu(p)` seen by other CPUs: not guaranteed stable with
  `CONFIG_SCHED_PROXY_EXEC`. `proxy_migrate_task()` can move a blocked
  migration-disabled task to another runqueue; `try_to_wake_up()` returns it.
- `affine_move_task()` for a task that is on a CPU or in `TASK_WAKING`: does
  not test `is_migration_disabled()`. It queues `migration_cpu_stop()`, which
  makes the test, leaves the request pending and clears `stop_pending`.
- `affine_move_task()` for a task that is neither: tests
  `is_migration_disabled()` itself, skips `move_queued_task()` and waits.
- CPU offline: the wait for `rq->nr_pinned` to reach zero is in
  `balance_hotplug_wait()`, under `CONFIG_HOTPLUG_CPU`. `balance_push()` does
  not wait; it wakes that waiter.
