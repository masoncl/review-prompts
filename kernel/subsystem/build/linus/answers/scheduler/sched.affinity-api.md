- `p->cpus_ptr` under migration disable: narrowed only after the task entered
  `__schedule()`; see "CPU mask under migration disable".
- `p->user_cpus_ptr`: an affinity change writes it only with `SCA_USER`.
  `sched_setaffinity()` sets it; `set_cpus_allowed_force()` resets it to
  NULL. `task_user_cpus()` returns `cpu_possible_mask` when it is NULL.
- `p->user_cpus_ptr` contents: protected by `p->pi_lock`; see
  `dup_user_cpus_ptr()`.
- `set_cpus_allowed_ptr()` on a task with `p->user_cpus_ptr`:
  `__set_cpus_allowed_ptr()` replaces the requested mask by its intersection
  with `p->user_cpus_ptr`, unless that is empty. `p->cpus_mask` can end up
  narrower than requested.
- `do_set_cpus_allowed()`: static in `kernel/sched/core.c`. Outside callers
  use `set_cpus_allowed_force()`, which needs `p->pi_lock` held by the
  caller, as `__kthread_bind_mask()` does.
- `-EINVAL` for a mask outside the allowed CPUs: the test is
  `cpumask_subset()` against `task_cpu_possible_mask()`, for non-kthreads
  only. There is no per-CPU kthread test.
- `-EINVAL` for `cpu_active_mask`: only when the mask has no CPU in it; the
  mask need not be a subset. Kthreads and migration-disabled tasks are tested
  against `cpu_online_mask` instead.
- `dl_task_check_affinity()` (`-EBUSY`) and the cpuset intersection: in
  `__sched_setaffinity()` in `kernel/sched/syscalls.c`, before
  `__set_cpus_allowed_ptr()` is called. Kernel callers of
  `set_cpus_allowed_ptr()` get neither.
- Equal mask without `SCA_MIGRATE_ENABLE`: returns 0 at once and does not
  wait. With `SCA_USER` it still swaps `p->user_cpus_ptr`.
- `affine_move_task()` `-EINVAL`: returned with a warning when no
  `p->migration_pending` exists after the install step.
- `affine_move_task()` returns without waiting when `task_cpu(p)` is in
  `&p->cpus_mask`, when `p` is the runqueue's donor but not its current task,
  or when `SCA_MIGRATE_ENABLE` is set and the task is on a CPU.
- Second wait in `affine_move_task()`: after `wait_for_completion()`, the
  caller that installed `my_pending` waits in `wait_var_event()` until every
  later caller has dropped its reference.
